from pydantic import Field
from pydantic_settings import BaseSettings


class SharedSettings(BaseSettings):
    SUPER_ADMIN_IDS: list[int] = Field(
        default_factory=lambda: [727941152, 156512090],
    )


class MailingSettings(BaseSettings):
    THROTTLER_RATE_LIMIT: int = 23


shared_settings = SharedSettings()
mailing_settings = MailingSettings()
