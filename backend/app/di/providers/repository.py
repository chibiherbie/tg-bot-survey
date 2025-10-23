from dishka import Provider, Scope
from repositories.checklist import (
    ChecklistAnswerRepository,
    ChecklistGroupRepository,
    ChecklistQuestionRepository,
    ChecklistRepository,
    ChecklistSessionRepository,
    EmployeeRepository,
    PositionRepository,
)
from repositories.settings import AppSettingRepository
from repositories.user import UserRepository

repository_provider = Provider(scope=Scope.REQUEST)
repository_provider.provide_all(
    UserRepository,
    PositionRepository,
    EmployeeRepository,
    ChecklistRepository,
    ChecklistQuestionRepository,
    ChecklistSessionRepository,
    ChecklistAnswerRepository,
    ChecklistGroupRepository,
    AppSettingRepository,
)
