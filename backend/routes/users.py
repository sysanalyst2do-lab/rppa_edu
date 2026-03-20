import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..db import get_pool

router = APIRouter()


def _row_to_dict(row) -> dict:
    d = dict(row)
    if "created_at" in d and d["created_at"] is not None:
        d["created_at"] = d["created_at"].isoformat()
    return d


@router.get("/api/users")
async def get_users(request: Request):
    pool = get_pool()
    id_param = request.query_params.get("id")

    if id_param is not None:
        try:
            uid = int(id_param)
        except ValueError:
            return JSONResponse({"error": "id must be integer"}, status_code=400)

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, email, created_at FROM users WHERE id = $1", uid
            )
        return {"user": _row_to_dict(row) if row else None}

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, name, email, created_at FROM users ORDER BY id DESC"
        )
    return {"users": [_row_to_dict(r) for r in rows]}


@router.post("/api/users")
async def create_user(request: Request):
    pool = get_pool()
    body = await _safe_json(request)

    name = str(body.get("name", "")).strip()
    email = str(body.get("email", "")).strip()

    if not name or not email:
        return JSONResponse(
            {"error": "name and email are required"}, status_code=400
        )

    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING id",
                name, email,
            )
        except Exception as e:
            if "unique" in str(e).lower():
                return JSONResponse(
                    {"error": "email already exists"}, status_code=409
                )
            raise

    return JSONResponse({"ok": True, "id": row["id"]}, status_code=201)


@router.put("/api/users")
async def update_user(request: Request):
    pool = get_pool()
    body = await _safe_json(request)

    try:
        uid = int(body["id"])
    except (KeyError, TypeError, ValueError):
        return JSONResponse({"error": "id must be integer"}, status_code=400)

    fields, params, idx = [], [], 1
    for col in ("name", "email"):
        val = body.get(col)
        if val is not None:
            val = str(val).strip()
            if val:
                fields.append(f"{col} = ${idx}")
                params.append(val)
                idx += 1

    if not fields:
        return JSONResponse({"error": "nothing to update"}, status_code=400)

    params.append(uid)
    sql = f"UPDATE users SET {', '.join(fields)} WHERE id = ${idx}"

    async with pool.acquire() as conn:
        try:
            result = await conn.execute(sql, *params)
        except Exception as e:
            if "unique" in str(e).lower():
                return JSONResponse(
                    {"error": "email already exists"}, status_code=409
                )
            raise

    if result.endswith(" 0"):
        return JSONResponse({"error": "not found"}, status_code=404)
    return {"ok": True}


@router.delete("/api/users")
async def delete_user(request: Request):
    pool = get_pool()
    id_raw = request.query_params.get("id")

    if id_raw is None:
        body = await _safe_json(request)
        id_raw = body.get("id")

    try:
        uid = int(id_raw)
    except (TypeError, ValueError):
        return JSONResponse({"error": "id must be integer"}, status_code=400)

    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM users WHERE id = $1", uid)

    if result.endswith(" 0"):
        return JSONResponse({"error": "not found"}, status_code=404)
    return {"ok": True}


async def _safe_json(request: Request) -> dict:
    ct = request.headers.get("content-type", "")
    if "application/json" not in ct:
        return {}
    body = await request.body()
    if not body:
        return {}
    return json.loads(body)
