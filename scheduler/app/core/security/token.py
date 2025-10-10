from core.config import core_settings
from jose import jwt

from shared.schemas.token import TokenSchema


def create_jwt_token(data: TokenSchema) -> str:
    return jwt.encode(
        data.model_dump(mode="json"),
        core_settings.JWT_KEY.get_secret_value(),
        algorithm="HS256",
    )
