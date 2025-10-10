from entities.user.models import User
from repositories.base import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)
