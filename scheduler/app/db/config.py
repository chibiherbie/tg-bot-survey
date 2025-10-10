from pydantic_settings import BaseSettings


class RedisSettings(BaseSettings):
    HOST: str = "redis"
    PORT: int = 6379
    DB: int = 0

    @property
    def dsn(self) -> str:
        return f"redis://{self.HOST}:{self.PORT}/{self.DB}"


redis_settings = RedisSettings()
