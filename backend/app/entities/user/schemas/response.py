from entities.user.schemas.base import UserBaseSchema
from shared.schemas.base import ResponseModel


class UserSchema(ResponseModel, UserBaseSchema):
    pass
