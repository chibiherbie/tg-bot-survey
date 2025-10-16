from enum import auto

from shared.enums.base import SameCaseStrEnum


class Group(SameCaseStrEnum):
    USER = auto()
    ADMIN = auto()
