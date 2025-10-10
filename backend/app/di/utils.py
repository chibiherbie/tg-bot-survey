from di.providers import (
    client_provider,
    interactor_provider,
    repository_provider,
    service_provider,
    session_provider,
    tools_provider,
)
from dishka import make_async_container


def create_container():
    return make_async_container(
        client_provider,
        interactor_provider,
        repository_provider,
        service_provider,
        session_provider,
        tools_provider,
    )
