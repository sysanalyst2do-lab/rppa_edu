import hashlib
import json
import os
import re
import secrets
import time
from urllib.parse import quote

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from ..db import get_pool
from ..mailer import send_email

router = APIRouter(prefix="/api/auth")


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _gen_code() -> str:
    return str(secrets.randbelow(900000) + 100000)


def _derive_name(email: str) -> str:
    local = email.split("@")[0] if "@" in email else ""
    if not local:
        return "User"
    name = re.sub(r"[._\-]+", " ", local)
    return name.title()


@router.post("/request-code")
async def request_code(request: Request):
    body = await _safe_json(request)
    email = str(body.get("email", "")).strip().lower()
    name_raw = str(body.get("name", "")).strip()

    if not email or "@" not in email:
        return JSONResponse({"error": "valid email required"}, status_code=400)

    pool = get_pool()

    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id, name FROM users WHERE email = $1", email
        )
        if not existing:
            name = name_raw or _derive_name(email)
            await conn.execute(
                "INSERT INTO users (name, email) VALUES ($1, $2)", name, email
            )

    code = _gen_code()
    code_hash = _sha256(code)
    now = int(time.time())
    ttl = 10 * 60

    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO auth_codes (email, code_hash, expires_at, created_at) "
            "VALUES ($1, $2, $3, $4)",
            email, code_hash, now + ttl, now,
        )

    text = f"Your verification code: {code}\nIt expires in 10 minutes."
    await send_email(email, "Your login code", text)

    result: dict = {"ok": True}
    if os.environ.get("DEV_DELIVERY") == "true":
        result["demo_code"] = code
    return result


@router.post("/verify-code")
async def verify_code(request: Request):
    body = await _safe_json(request)
    email = str(body.get("email", "")).strip().lower()
    code = str(body.get("code", "")).strip()

    if not email or not code:
        return JSONResponse({"error": "email and code required"}, status_code=400)

    code_hash = _sha256(code)
    now = int(time.time())
    pool = get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT email, expires_at FROM auth_codes "
            "WHERE email = $1 AND code_hash = $2 ORDER BY created_at DESC LIMIT 1",
            email, code_hash,
        )

    if not row or row["expires_at"] < now:
        return JSONResponse({"error": "invalid or expired code"}, status_code=400)

    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, name FROM users WHERE email = $1", email
        )

    name = user["name"] if user else "User"

    sid = secrets.token_hex(32)
    exp = now + 7 * 24 * 60 * 60

    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO sessions (session_id, email, expires_at, created_at) "
            "VALUES ($1, $2, $3, $4)",
            sid, email, exp, now,
        )

    resp = JSONResponse({"ok": True})
    resp.set_cookie(
        "sid", sid,
        path="/", max_age=7 * 24 * 60 * 60, httponly=True, samesite="lax",
    )
    u_value = quote(json.dumps({"email": email, "name": name}))
    resp.set_cookie(
        "u", u_value,
        path="/", max_age=7 * 24 * 60 * 60, httponly=False, samesite="lax",
    )
    return resp


@router.post("/logout")
async def logout(request: Request):
    sid = request.cookies.get("sid")

    if sid:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM sessions WHERE session_id = $1", sid
            )

    resp = JSONResponse({"ok": True})
    resp.delete_cookie("sid", path="/")
    resp.delete_cookie("u", path="/")
    return resp


async def _safe_json(request: Request) -> dict:
    ct = request.headers.get("content-type", "")
    if "application/json" not in ct:
        return {}
    body = await request.body()
    if not body:
        return {}
    return json.loads(body)
