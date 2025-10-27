from datetime import UTC, datetime

from core.security.globals import TOKEN_EXPIRE_IN
from pydantic import BaseModel, Field, field_serializer
from shared.enums.group import Group


class TokenSchema(BaseModel):
    client_id: str | None = None
    user_id: int | None = None
    groups: list[Group]
    expires_in: datetime = Field(
        default_factory=lambda: datetime.now(UTC) + TOKEN_EXPIRE_IN,
    )

    @field_serializer("expires_in")
    def serialize_expires_in(self, expires_in: datetime):
        return int(expires_in.timestamp())
