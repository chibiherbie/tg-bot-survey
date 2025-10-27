from enum import auto

from shared.enums.base import SameCaseStrEnum


class HealthStatus(SameCaseStrEnum):
    OK = auto()
    DEGRADED = auto()
    SHUTDOWN = auto()
    FAIL = auto()
    CRITICAL = auto()
