import json
import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..db import get_pool

router = APIRouter()


@router.post("/api/orders")
async def create_order(request: Request):
    pool = get_pool()

    user = await _get_current_user(request)
    if not user:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    body = await _safe_json(request)
    items = body.get("items") if isinstance(body.get("items"), list) else []
    if not items:
        return JSONResponse({"error": "items required"}, status_code=400)

    wanted: list[dict] = []
    seen: dict[int, int] = {}
    for it in items:
        try:
            pid = int(it["product_id"])
            qty = int(it["qty"])
            assert qty > 0
        except (KeyError, TypeError, ValueError, AssertionError):
            return JSONResponse(
                {"error": "invalid items: product_id integer, qty positive integer"},
                status_code=400,
            )

        if pid in seen:
            wanted[seen[pid]]["qty"] += qty
        else:
            seen[pid] = len(wanted)
            wanted.append({"product_id": pid, "qty": qty})

    ids = [w["product_id"] for w in wanted]
    placeholders = ", ".join(f"${i + 1}" for i in range(len(ids)))

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT id, name, price_cents FROM products WHERE id IN ({placeholders})",
            *ids,
        )

    found = {r["id"]: r for r in rows}
    missing = [pid for pid in ids if pid not in found]
    if missing:
        return JSONResponse(
            {"error": f"products not found: {','.join(map(str, missing))}"},
            status_code=400,
        )

    items_map: dict = {}
    total_cents = 0
    for w in wanted:
        p = found[w["product_id"]]
        price = p["price_cents"] or 0
        line = price * w["qty"]
        total_cents += line
        items_map[str(w["product_id"])] = {
            "qty": w["qty"],
            "price_cents": price,
            "line_total_cents": line,
            "name": p["name"],
        }

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO orders (user_id, items_json, total_cents) "
            "VALUES ($1, $2::jsonb, $3) RETURNING id, created_at",
            user["user_id"], json.dumps(items_map), total_cents,
        )

    return JSONResponse(
        {
            "ok": True,
            "order": {
                "id": row["id"],
                "user_id": user["user_id"],
                "total_cents": total_cents,
                "created_at": row["created_at"].isoformat(),
                "items_map": items_map,
            },
        },
        status_code=201,
    )


async def _get_current_user(request: Request) -> dict | None:
    sid = request.cookies.get("sid")
    if not sid:
        return None

    pool = get_pool()
    async with pool.acquire() as conn:
        session = await conn.fetchrow(
            "SELECT email, expires_at FROM sessions WHERE session_id = $1", sid
        )

    if not session or session["expires_at"] < int(time.time()):
        return None

    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, name FROM users WHERE email = $1", session["email"]
        )
    if not user:
        return None

    return {"user_id": user["id"], "email": session["email"], "name": user["name"]}


async def _safe_json(request: Request) -> dict:
    ct = request.headers.get("content-type", "")
    if "application/json" not in ct:
        return {}
    body = await request.body()
    if not body:
        return {}
    return json.loads(body)
