"""Global exception handlers — structured error responses, no leaked tracebacks."""

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)


class RequestIDMiddleware:
    """Attach a unique request ID to every request for traceability.

    Implemented as a pure ASGI middleware (not BaseHTTPMiddleware) to avoid
    known Starlette issues where BaseHTTPMiddleware swallows CORS headers
    on error responses.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        # Store on scope so downstream code can access via request.state
        scope.setdefault("state", {})["request_id"] = request_id

        async def send_with_request_id(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_request_id)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ):
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "detail": exc.errors(),
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "detail": str(exc),
            },
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        logger.error("DB integrity error: %s", exc)
        return JSONResponse(
            status_code=409,
            content={
                "error": "conflict",
                "detail": "A database constraint was violated.",
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception")
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "detail": "An unexpected error occurred.",
            },
        )
