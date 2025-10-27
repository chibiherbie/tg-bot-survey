from collections.abc import Sequence

from entities.user.exceptions.statuses import (
    UserRegistrationStatusInvalidTransactionError,
)
from entities.user.models import User
from entities.user.schemas.forms import (
    UserAdminFlagPatchSchema,
    UserPatchSchema,
    UserPutSchema,
    UserRegistrationStatusPatchSchema,
    UserResetSchema,
)
from repositories.user import UserRepository
from services.base import BaseService
from services.telegram import TelegramService


class UserService(BaseService):
    def __init__(
        self,
        user_repository: UserRepository,
        telegram_service: TelegramService,
    ):
        self.user_repository = user_repository
        self.telegram_service = telegram_service

    async def get_users(self) -> Sequence[User]:
        return await self.user_repository.list()

    async def put_user(
        self,
        put_schema: UserPutSchema | UserResetSchema,
    ) -> tuple[User, bool]:
        if not (obj := await self.get_user_or_none(user_id=put_schema.id)):
            user, created = (
                await self.user_repository.create(
                    put_schema.model_dump(
                        exclude_unset=True,
                    ),
                ),
                True,
            )
        else:
            user, created = (
                await self.user_repository.update(
                    obj,
                    put_schema.model_dump(
                        exclude_unset=True,
                        exclude={
                            "id",
                        },
                    ),
                ),
                False,
            )
        return user, created

    async def update_user_admin_flag(
        self,
        user: User,
        admin_flag: bool,
    ) -> User:
        admin_flag_patch_schema = UserAdminFlagPatchSchema(
            admin_flag=admin_flag,
        )
        return await self.user_repository.update(
            user,
            admin_flag_patch_schema.model_dump(),
        )

    async def patch_user(
        self,
        user: User,
        patch_schema: UserPatchSchema,
    ) -> User:
        return await self.user_repository.update(
            user,
            patch_schema.model_dump(
                exclude_unset=True,
            ),
        )

    async def patch_user_registration_status(
        self,
        user: User,
        patch_schema: UserRegistrationStatusPatchSchema,
    ) -> None:
        if user.registration_status == patch_schema.registration_status:
            return

        def validate_transaction():
            pass

        def raise_invalid_transition():
            raise UserRegistrationStatusInvalidTransactionError()

        async def process_transaction():
            await self.user_repository.update(user, patch_schema.model_dump())

        valid_transitions = {
            """
            For Example DELETE IN REAL PROJECT
            (
                UserRegistrationStatus.UNKNOWN,
                UserRegistrationStatus.REGISTERED
            ): dict(is_registered=True),
            """,
        }
        transaction = (
            user.registration_status,
            patch_schema.registration_status,
        )
        if transaction in valid_transitions:
            validate_transaction()
            await process_transaction()
        else:
            raise_invalid_transition()
        return

    async def get_user_or_none(
        self,
        user_id: int,
    ) -> User | None:
        return await self.user_repository.get(user_id)

    async def reset_user(self, user: User) -> User:
        await self.user_repository.delete(user.id)
        user, _ = await self.put_user(
            UserResetSchema.model_validate(user, from_attributes=True),
        )
        return user
