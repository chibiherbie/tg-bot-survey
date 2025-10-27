from abc import ABC, abstractmethod
from typing import TypeVar

from dto.base import BaseDTO

D = TypeVar("D", bound=BaseDTO)


class BaseInteractor[D](ABC):
    @abstractmethod
    async def execute(self, dto: D) -> None:
        pass
