from dishka import Provider, Scope
from interactors.debug import DebugInteractor

interactor_provider = Provider(scope=Scope.REQUEST)
interactor_provider.provide_all(
    DebugInteractor,
)
