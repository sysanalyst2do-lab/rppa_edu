import logging
import os
from pathlib import Path

import asyncpg

log = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def init_pool():
    global _pool
    dsn = os.environ["DATABASE_URL"]
    log.info("Connecting to DB at %s", dsn.split("@")[-1])
    _pool = await asyncpg.create_pool(dsn, min_size=1, max_size=10, timeout=60, command_timeout=60)

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
