from pydantic import BaseModel


class BotInfoSchema(BaseModel):
    id: int
    username: str | None
