import json
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject
from core.logs import logger


class TelegramLoggingMiddleware(BaseMiddleware):
    """Log polling updates in the same format as HTTP webhook requests."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        structlog.contextvars.clear_contextvars()

        request_id = str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)

        log_params = {
            "path": "/telegram/polling",
            "query": "",
            "method": "UPDATE",
            "headers": {},
            "peer_id": self._resolve_peer_id(event),
            "request_body": self._dump_event(event),
        }
        logger.info("Request received", **log_params)
        try:
            result = await handler(event, data)
        except Exception:
            logger.exception("Unhandled exception during request processing")
            raise
        structlog.contextvars.bind_contextvars(status_code=200, headers={})
        logger.info("Response processed", **log_params)
        return result

    @staticmethod
    def _resolve_peer_id(event: TelegramObject) -> int | None:
        user = getattr(event, "from_user", None)
        if user is not None:
            return getattr(user, "id", None)
        chat = getattr(event, "chat", None)
        if chat is not None:
            return getattr(chat, "id", None)
        return None

    @staticmethod
    def _dump_event(event: TelegramObject) -> str:
        if hasattr(event, "model_dump"):
            return json.dumps(
                event.model_dump(exclude_none=True),
                default=str,
            )
        return str(event)
