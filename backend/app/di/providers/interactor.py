from dishka import Provider, Scope
from interactors.debug import DebugInteractor
from interactors.mailings import MailingsInteractor

interactor_provider = Provider(scope=Scope.REQUEST)
interactor_provider.provide_all(
    DebugInteractor,
    MailingsInteractor,
)
