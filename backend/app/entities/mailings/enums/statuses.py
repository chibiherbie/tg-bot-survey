from enum import auto

from shared.enums.base import SameCaseStrEnum


class MailingStatus(SameCaseStrEnum):
    CREATED = auto()
    PENDING = auto()
    RESUME = auto()
    SENDING = auto()
    PAUSED = auto()
    SENT = auto()
    FAILED = auto()
