from entities.user.models import User
from entities.user.schemas.forms import (
    UserReferrerUpdateSchema,
    UserUTMUpdateSchema,
)
from fastapi import HTTPException, status
from repositories.user import UserRepository
from services.base import BaseService
from services.user import UserService


class ReferralSystemService(BaseService):
    def __init__(
        self,
        user_service: UserService,
        user_repository: UserRepository,
    ):
        self.user_service = user_service
        self.user_repository = user_repository

    async def assign_referrer(
        self,
        user: User,
        referrer_patch_schema: UserReferrerUpdateSchema,
    ) -> None:
        if user.referrer_id is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already has a referrer",
            )
        if referrer_patch_schema.referrer_id == user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Referrer ID cannot be the same as the user ID",
            )
        if not await self.user_repository.exists(
            referrer_patch_schema.referrer_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Referrer ID does not exist",
            )
        await self.user_repository.update(
            user,
            referrer_patch_schema.model_dump(exclude_unset=True),
        )

    async def assign_utm(
        self,
        user: User,
        utm_patch_schema: UserUTMUpdateSchema,
    ) -> None:
        if user.utm is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already has a UTM",
            )
        await self.user_repository.update(
            user,
            utm_patch_schema.model_dump(exclude_unset=True),
        )
