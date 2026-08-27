import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def _catch_unhandled_exceptions(request: Request, call_next):  # type: ignore[no-untyped-def]
    # A bare `@app.exception_handler(Exception)` looks like the fix here, but
    # isn't: FastAPI wires it up as the handler for Starlette's *outer*
    # ServerErrorMiddleware (added via `error_handler=` in
    # build_middleware_stack), which sits OUTSIDE CORSMiddleware and always
    # sends its response through the raw ASGI `send` it was given — never
    # back through CORSMiddleware. So the browser sees a 500 with no
    # Access-Control-Allow-Origin header and reports a misleading "CORS
    # policy" error instead of the real failure. This middleware is added
    # (see below) *before* CORSMiddleware, which — because Starlette's
    # add_middleware() prepends — makes it sit *inside* CORSMiddleware in the
    # final stack, so a response built here still passes through CORS header
    # injection on the way out.
    try:
        return await call_next(request)
    except Exception as exc:
        logger.exception("Unhandled exception", exc_info=exc)
        return JSONResponse(status_code=500, content={"detail": "internal_server_error"})


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title=settings.app_name)

    app.middleware("http")(_catch_unhandled_exceptions)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
