from collections.abc import AsyncGenerator
from typing import Any

from aiogram.client.session.aiohttp import (
    AiohttpSession as AiogramAiohttpSession,
)
from aiohttp import ClientSession as AiohttpClientSession
from core.config import core_settings
from db.config import postgres_settings, redis_settings
from dishka import Provider, Scope, provide
from httpx import AsyncClient as HttpxAsyncClient
from openai import AsyncOpenAI
from openai.types.beta import Thread
from redis.asyncio import Redis
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
    async def get_httpx_async_client(
        self,
    ) -> AsyncGenerator[HttpxAsyncClient, Any]:
        kwargs = {}
        if core_settings.HTTPX_PROXY:
            kwargs.update(proxy=core_settings.HTTPX_PROXY.get_secret_value())
        client = HttpxAsyncClient(**kwargs)
        yield client
        await client.aclose()

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

    @provide(scope=Scope.APP)
    def get_openai_session(
        self,
        httpx_session: HttpxAsyncClient,
    ) -> AsyncOpenAI:
        token = core_settings.OPENAI_API_TOKEN.get_secret_value()
        if token is None:
            raise ValueError("OPENAI_API_TOKEN is not set")  # noqa: TRY003
        return AsyncOpenAI(
            api_key=token,
            http_client=httpx_session,
        )

    @provide(scope=Scope.REQUEST)
    async def get_thread(
        self,
        openai_client: AsyncOpenAI,
    ) -> AsyncGenerator[Thread, Any]:
        thread = await openai_client.beta.threads.delete()
        yield thread
        if core_settings.DELETE_OPENAI_THREADS:
            await openai_client.beta.threads.delete(thread.id)

    @provide(scope=Scope.APP)
    async def redis_provider(self) -> AsyncGenerator[Redis, Any]:
        redis = Redis.from_url(redis_settings.dsn)
        yield redis
        await redis.aclose()


session_provider = SessionProvider()
