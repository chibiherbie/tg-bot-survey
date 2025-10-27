from core.config import core_settings
from pydantic import SecretStr
from pydantic_settings import BaseSettings
from yarl import URL


class TelegramSettings(BaseSettings):
    TELEGRAM_BOT_TOKEN: SecretStr

    TELEGRAM_SECRET_TOKEN: SecretStr

    TELEGRAM_ADMIN_CHAT_ID: int
    TELEGRAM_SERVICE_CHAT_ID: int
    TELEGRAM_USE_WEBHOOK: bool = False

    @property
    def webhook_url(self) -> URL:
        return core_settings.v1_api_url / "telegram" / "webhook"

    @property
    def telegram_url(self) -> URL:
        return URL("t.me")


telegram_settings = TelegramSettings()
