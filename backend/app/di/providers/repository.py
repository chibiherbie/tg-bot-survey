from dishka import Provider, Scope
from repositories.mailings import MailingRepository
from repositories.user import UserRepository

repository_provider = Provider(scope=Scope.REQUEST)
repository_provider.provide_all(
    MailingRepository,
    UserRepository,
)
