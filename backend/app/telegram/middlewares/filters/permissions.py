from typing import Any

from aiogram.filters import Filter
from entities.user.models import User
from shared.enums.group import Group


class GroupFilter(Filter):
    def __init__(self, group: Group) -> None:
        self.group = group

    async def __call__(self, _: Any, user: User) -> bool:
        match self.group:
            case Group.ADMIN:
                return user.is_admin
            case Group.USER:
                return not user.is_banned
            case _:
                raise NotImplementedError
