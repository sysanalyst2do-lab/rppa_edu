import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from .db import close_pool, get_pool, init_pool
from .routes import auth, orders, products, users

ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "temp2026")

OPEN_EXACT = frozenset(
    {
        "/",
        "/index.html",
        "/login",
        "/login.html",
        "/api/auth/request-code",
        "/api/auth/verify-code",
        "/api/auth/logout",
    }
)
OPEN_PREFIX = ("/assets/", "/favicon", "/robots.txt", "/site.webmanifest", "/api/admin/")


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if request.method == "OPTIONS":
            return await call_next(request)

        is_open = path in OPEN_EXACT or any(path.startswith(p) for p in OPEN_PREFIX)
        if is_open:
            return await call_next(request)

        sid = request.cookies.get("sid")
        if not sid:
            return _deny(request)

        try:
            pool = get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT email, expires_at FROM sessions WHERE session_id = $1",
                    sid,
                )
            if not row or row["expires_at"] < int(time.time()):
                return _deny(request)
        except Exception:
            return _deny(request)

        return await call_next(request)


def _deny(request: Request):
    path = request.url.path
    if path.startswith("/api/"):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    next_path = path + (f"?{request.url.query}" if request.url.query else "")
    if next_path.startswith("/login"):
        next_path = "/"
    return RedirectResponse(
        f"/login.html?next={quote(next_path)}", status_code=302
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_pool()
    yield
    await close_pool()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(AuthMiddleware)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(orders.router)


@app.get("/hello")
async def hello():
    return "hello"


@app.get("/api/admin/query")
async def admin_query(secret: str = "", sql: str = ""):
    if not ADMIN_SECRET or secret != ADMIN_SECRET:
        return JSONResponse({"error": "forbidden"}, status_code=403)
    if not sql:
        return JSONResponse({"error": "sql parameter required"}, status_code=400)
    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql)
            result = [dict(r) for r in rows]
            for row in result:
                for k, v in row.items():
                    if not isinstance(v, (str, int, float, bool, type(None))):
                        row[k] = str(v)
            return {"rows": result, "count": len(result)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


static_dir = Path(__file__).resolve().parent.parent / "public"
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
        reload=True,
    )
