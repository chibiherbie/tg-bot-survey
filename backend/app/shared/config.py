from pydantic import Field
from pydantic_settings import BaseSettings


class SharedSettings(BaseSettings):
    SUPER_ADMIN_IDS: list[int] = Field(
        default_factory=lambda: [727941152, 156512090],
    )


shared_settings = SharedSettings()
