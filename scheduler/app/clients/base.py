from typing import TypeVar, overload

from aiohttp import ClientResponse, ClientSession
from core.security.globals import HEADER_TOKEN_KEY
from core.security.token import create_jwt_token
from pydantic import BaseModel, TypeAdapter, ValidationError
from yarl import URL

from shared.enums.group import Group
from shared.enums.request import RequestMethod
from shared.schemas.token import TokenSchema

T = TypeVar("T", bound=BaseModel)


class BaseInnerClient:
    client_id: str
    base_url: URL

    def __init__(self, session: ClientSession):
        self.session = session
        self.client_id = self.client_id
        self.base_url = self.base_url

    @overload
    async def request(
        self,
        url: URL,
        *,
        method: RequestMethod,
        schema: BaseModel | dict | None = None,
        response_type: None = None,
    ) -> ClientResponse: ...
    @overload
    async def request(
        self,
        url: URL,
        *,
        method: RequestMethod,
        schema: BaseModel | dict | None = None,
        response_type: type[T],
    ) -> T: ...
    async def request(
        self,
        url: URL,
        *,
        method: RequestMethod,
        schema: BaseModel | dict | None = None,
        response_type: type[T] | None = None,
    ) -> T | ClientResponse:
        json = (
            schema.model_dump(mode="json")
            if isinstance(schema, BaseModel)
            else schema
        )

        response = await self.session.request(
            method,
            url,
            json=json,
            headers=self.headers,
        )
        response.raise_for_status()

        if not response_type:
            return response

        adapter = TypeAdapter(response_type)
        text = await response.text()
        try:
            model = adapter.validate_json(text)
        except ValidationError as e:
            try:
                model = adapter.validate_strings(text)
            except ValidationError as inner_e:
                raise e from inner_e
        return model

    @property
    def headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **self.service_token_headers,
        }

    @property
    def service_token(self) -> str:
        return create_jwt_token(
            TokenSchema(
                client_id=self.client_id,
                groups=[Group.SERVICE],
            ),
        )

    @property
    def service_token_headers(self) -> dict:
        return {HEADER_TOKEN_KEY: self.service_token}
