import uuid
from collections.abc import Callable, Coroutine
from typing import Any

import structlog
from core.logs import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Coroutine[Any, Any, Response]],
    ) -> Response:
        structlog.contextvars.clear_contextvars()

        request_id = str(uuid.uuid4())

        structlog.contextvars.bind_contextvars(request_id=request_id)

        log_params = {
            "path": request.url.path,
            "query": request.url.query,
            "method": request.method,
            "headers": dict(request.headers.items()),
            "peer_id": request.client.host
            if request.client is not None
            else None,
            "request_body": (await request.body()).decode(),
        }
        logger.info("Request received", **log_params)
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("Unhandled exception during request processing")
            raise
        structlog.contextvars.bind_contextvars(
            status_code=response.status_code,
            headers=dict(response.headers.items()),
        )
        logger.info("Response processed", **log_params)
        return response
