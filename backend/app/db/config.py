from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class PostgresSettings(BaseSettings):
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: SecretStr = Field(...)
    POSTGRES_DB: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_HOST: str = "database"
    ENGINE: str = "postgresql"

    @property
    def url_template(self) -> str:
        return "{engine}://{user}:{password}@{host}:{port}/{database}"

    @property
    def sync_url(self) -> str:
        return self.url_template.format(
            engine=self.ENGINE,
            user=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD.get_secret_value(),
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )

    @property
    def async_url(self) -> str:
        return self.url_template.format(
            engine=f"{self.ENGINE}+asyncpg",
            user=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD.get_secret_value(),
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )


postgres_settings = PostgresSettings()
