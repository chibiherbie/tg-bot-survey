from typing import Annotated

from asgi.dependence.security import CurrentUserDependency
from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from entities.user.enums.statuses import UserRegistrationStatus
from entities.user.schemas.forms import (
    UserReferrerUpdateSchema,
    UserRegistrationStatusPatchSchema,
    UserUTMUpdateSchema,
)
from entities.user.schemas.response import UserSchema
from fastapi import APIRouter, Body
from services.referral_system import ReferralSystemService
from services.user import UserService

router = APIRouter(prefix="/user", tags=["user"], route_class=DishkaRoute)


@router.post("/referrer")
async def assign_referrer(
    user: CurrentUserDependency,
    referral_system_service: FromDishka[ReferralSystemService],
    referrer_update_schema: UserReferrerUpdateSchema,
) -> None:
    await referral_system_service.assign_referrer(user, referrer_update_schema)


@router.post("/utm")
async def assign_utm(
    user: CurrentUserDependency,
    referral_system_service: FromDishka[ReferralSystemService],
    utm_update_schema: UserUTMUpdateSchema,
) -> None:
    await referral_system_service.assign_utm(user, utm_update_schema)


@router.get("/me")
async def user_me(user: CurrentUserDependency) -> UserSchema:
    return UserSchema.model_validate(user, from_attributes=True)


@router.patch("/me/registration-status")
async def registration_status_patch(
    user: CurrentUserDependency,
    user_service: FromDishka[UserService],
    new_status: Annotated[UserRegistrationStatus, Body(...)],
) -> None:
    await user_service.patch_user_registration_status(
        user,
        UserRegistrationStatusPatchSchema(registration_status=new_status),
    )
