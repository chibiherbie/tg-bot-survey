from collections.abc import AsyncGenerator
from typing import Any

from aiogram.client.session.aiohttp import (
    AiohttpSession as AiogramAiohttpSession,
)
from aiohttp import ClientSession as AiohttpClientSession
from db.config import postgres_settings
from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class SessionProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_aiohttp_client_session(
        self,
    ) -> AsyncGenerator[AiohttpClientSession, Any]:
        session = AiohttpClientSession()
        yield session
        await session.close()

    @provide(scope=Scope.APP)
    async def get_aiogram_aiohttp_session(
        self,
    ) -> AsyncGenerator[AiogramAiohttpSession, Any]:
        session = AiogramAiohttpSession()
        yield session
        await session.close()

    @provide(scope=Scope.APP)
    async def get_async_engine(self) -> AsyncGenerator[AsyncEngine, Any]:
        engine = create_async_engine(postgres_settings.async_url)
        yield engine
        await engine.dispose()

    @provide(scope=Scope.APP)
    async def get_session_maker(
        self,
        async_engine: AsyncEngine,
    ) -> AsyncGenerator[async_sessionmaker[AsyncSession], Any]:
        session_maker = async_sessionmaker(async_engine)
        yield session_maker

    @provide(scope=Scope.REQUEST)
    async def get_db_session(
        self,
        session_maker: async_sessionmaker[AsyncSession],
    ) -> AsyncGenerator[AsyncSession, Any]:
        async with session_maker() as session:
            yield session


session_provider = SessionProvider()
