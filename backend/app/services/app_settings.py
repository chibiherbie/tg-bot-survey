from __future__ import annotations

import json
from typing import Any

from repositories.settings import AppSettingRepository
from services.base import BaseService


class AppSettingsService(BaseService):
    def __init__(self, repository: AppSettingRepository) -> None:
        self.repository = repository

    async def get_value(self, key: str) -> Any | None:
        setting = await self.repository.get_by_key(key)
        return setting.value if setting else None

    async def get_json(self, key: str, default: Any = None) -> Any:
        value = await self.get_value(key)
        if value is None:
            return default
        return value

    async def get_string(self, key: str, default: str | None = None) -> str | None:
        value = await self.get_value(key)
        if value is None:
            return default
        if isinstance(value, str):
            return value
        return json.dumps(value)
