import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..db import get_pool

router = APIRouter()


@router.get("/api/products")
async def get_products(request: Request):
    pool = get_pool()
    id_param = request.query_params.get("id")

    if id_param is not None:
        try:
            pid = int(id_param)
        except ValueError:
            return JSONResponse({"error": "id must be integer"}, status_code=400)

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, description, price_cents, image_url "
                "FROM products WHERE id = $1",
                pid,
            )
        return {"product": dict(row) if row else None}

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, name, description, price_cents, image_url "
            "FROM products ORDER BY id DESC"
        )
    return {"products": [dict(r) for r in rows]}


@router.post("/api/products")
async def create_product(request: Request):
    pool = get_pool()
    body = await _safe_json(request)

    name = str(body.get("name", "")).strip()
    description = str(body.get("description", "")).strip()
    price_raw = body.get("price_cents")
    image_url = body.get("image_url")
    if image_url is not None:
        image_url = str(image_url).strip() or None

    try:
        price_cents = int(price_raw)
        assert price_cents >= 0
    except (TypeError, ValueError, AssertionError):
        return JSONResponse(
            {"error": "name, description, price_cents (non-negative integer) are required"},
            status_code=400,
        )

    if not name or not description:
        return JSONResponse(
            {"error": "name, description, price_cents (non-negative integer) are required"},
            status_code=400,
        )

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO products (name, description, price_cents, image_url) "
            "VALUES ($1, $2, $3, $4) RETURNING id",
            name, description, price_cents, image_url,
        )

    return JSONResponse({"ok": True, "id": row["id"]}, status_code=201)


@router.put("/api/products")
async def update_product(request: Request):
    pool = get_pool()
    body = await _safe_json(request)

    try:
        pid = int(body["id"])
    except (KeyError, TypeError, ValueError):
        return JSONResponse({"error": "id must be integer"}, status_code=400)

    fields, params, idx = [], [], 1

    if body.get("name") is not None:
        val = str(body["name"]).strip()
        if val:
            fields.append(f"name = ${idx}")
            params.append(val)
            idx += 1

    if body.get("description") is not None:
        val = str(body["description"]).strip()
        if val:
            fields.append(f"description = ${idx}")
            params.append(val)
            idx += 1

    if body.get("price_cents") is not None:
        try:
            pc = int(body["price_cents"])
            assert pc >= 0
        except (TypeError, ValueError, AssertionError):
            return JSONResponse(
                {"error": "price_cents must be non-negative integer"},
                status_code=400,
            )
        fields.append(f"price_cents = ${idx}")
        params.append(pc)
        idx += 1

    if body.get("image_url") is not None:
        val = str(body["image_url"]).strip()
        fields.append(f"image_url = ${idx}")
        params.append(val or None)
        idx += 1

    if not fields:
        return JSONResponse({"error": "nothing to update"}, status_code=400)

    params.append(pid)
    sql = f"UPDATE products SET {', '.join(fields)} WHERE id = ${idx}"

    async with pool.acquire() as conn:
        result = await conn.execute(sql, *params)

    if result.endswith(" 0"):
        return JSONResponse({"error": "not found"}, status_code=404)
    return {"ok": True}


@router.delete("/api/products")
async def delete_product(request: Request):
    pool = get_pool()
    id_raw = request.query_params.get("id")

    if id_raw is None:
        body = await _safe_json(request)
        id_raw = body.get("id")

    try:
        pid = int(id_raw)
    except (TypeError, ValueError):
        return JSONResponse({"error": "id must be integer"}, status_code=400)

    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM products WHERE id = $1", pid)

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
