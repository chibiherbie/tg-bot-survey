from datetime import UTC, datetime

from core.config import core_settings
from fastapi import HTTPException
from jose import JWTError, jwt
from pydantic import ValidationError
from shared.schemas.token import TokenSchema
from starlette import status


def create_jwt_token(data: TokenSchema) -> str:
    return jwt.encode(
        data.model_dump(mode="json"),
        core_settings.JWT_KEY.get_secret_value(),
        algorithm="HS256",
    )


def parse_jwt_token(token: str) -> TokenSchema:
    data = jwt.decode(
        token,
        core_settings.JWT_KEY.get_secret_value(),
        algorithms=["HS256"],
    )
    return TokenSchema.model_validate(data)


def get_token(jwt_token: str | None) -> TokenSchema:
    if not jwt_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    try:
        token = parse_jwt_token(jwt_token)
        if token.expires_in <= datetime.now(UTC):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED) from e
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED) from e
    return token
