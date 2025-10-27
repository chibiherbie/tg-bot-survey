from entities.user.enums.statuses import UserRegistrationStatus
from entities.user.schemas.base import UserTelegramSchema
from shared.schemas.base import FormModel


class UserPutSchema(FormModel, UserTelegramSchema):
    pass


class UserRegistrationStatusPatchSchema(FormModel):
    registration_status: UserRegistrationStatus


class UserPatchSchema(FormModel):
    tg_username: str | None = None
    tg_first_name: str = None
    tg_last_name: str | None = None
    tg_bio: str | None = None
    tg_birthdate: str | None = None


class UserReferrerUpdateSchema(FormModel):
    referrer_id: int


class UserUTMUpdateSchema(FormModel):
    utm: str


class UserAdminFlagPatchSchema(FormModel):
    admin_flag: bool


class UserResetSchema(UserPutSchema, UserAdminFlagPatchSchema):
    pass
