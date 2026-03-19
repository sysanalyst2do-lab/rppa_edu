import os
from pathlib import Path

import asyncpg

_pool: asyncpg.Pool | None = None


async def init_pool():
    global _pool
    _pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=2, max_size=10)

    schema = Path(__file__).resolve().parent.parent / "schema.sql"
    if schema.exists():
        async with _pool.acquire() as conn:
            await conn.execute(schema.read_text(encoding="utf-8"))


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialized")
    return _pool
