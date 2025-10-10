from entities.user.enums.statuses import UserRegistrationStatus
from pydantic import BaseModel


class UserTelegramSchema(BaseModel):
    id: int
    tg_username: str | None
    tg_first_name: str
    tg_last_name: str | None
    tg_bio: str | None
    tg_birthdate: str | None


class UserBaseSchema(UserTelegramSchema):
    registration_status: UserRegistrationStatus
    admin_flag: bool
