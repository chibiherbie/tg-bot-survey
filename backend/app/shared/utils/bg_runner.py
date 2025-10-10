import asyncio
from typing import TypeVar

from core.logs import logger
from dishka import AsyncContainer, Scope
from dto.base import BaseDTO
from interactors.base import BaseInteractor

T = TypeVar("T", bound=BaseInteractor)
D = TypeVar("D", bound=BaseDTO)


class BgRunner:
    def __init__(self, container: AsyncContainer):
        self.container = container
        self.tasks: set[asyncio.Task] = set()

    async def queue_interactor(self, interactor: type[T], dto: D):
        coroutine = self.execute_interactor(interactor, dto)
        self.tasks.add(asyncio.create_task(coroutine))

    async def execute_interactor(self, interactor: T, dto: D):
        try:
            async with self.container(scope=Scope.REQUEST) as container:
                instance = await container.get(interactor)
                result = instance.execute(dto)
                if asyncio.iscoroutine(result):
                    await result
        except Exception as e:  # noqa: BLE001
            logger.exception(f"Error performing task: {e}", exc_info=e)
        finally:
            self.tasks.remove(asyncio.current_task())
