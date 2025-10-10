from enum import auto

from shared.enums.base import SameCaseStrEnum


class RequestMethod(SameCaseStrEnum):
    GET = auto()
    POST = auto()
    PATCH = auto()
    PUT = auto()
    DELETE = auto()
