from enum import Enum


class ChecklistAnswerValue(str, Enum):
    YES = "YES"
    NO = "NO"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ChecklistSessionStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
