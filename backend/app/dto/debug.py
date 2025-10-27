from dto.base import BaseDTO
from entities.user.schemas.forms import UserPutSchema


class DebugDTO(BaseDTO):
    users: list[UserPutSchema]
    message: str
