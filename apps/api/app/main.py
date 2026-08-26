import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # An exception with no registered handler escapes ExceptionMiddleware
        # (inside CORSMiddleware) up to Starlette's outer ServerErrorMiddleware,
        # which sends its 500 response without ever passing back through
        # CORSMiddleware — the browser then sees a response with no
        # Access-Control-Allow-Origin header and reports it as a CORS failure,
        # masking whatever actually broke. Catching it here keeps the response
        # inside the normal (CORS-wrapped) path.
        logger.exception("Unhandled exception", exc_info=exc)
        return JSONResponse(status_code=500, content={"detail": "internal_server_error"})

    return app


app = create_app()
