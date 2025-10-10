from pydantic import SecretStr
from pydantic_settings import BaseSettings
from yarl import URL


class CoreSettings(BaseSettings):
    PROCESSING_CLIENT_ID: str

    DEBUG: bool = False
    WORKERS: int = 1
    BACKEND_PORT: int = 5000

    DOMAIN: str
    JWT_KEY: SecretStr

    OPENAI_API_TOKEN: SecretStr | None = None
    DELETE_OPENAI_THREADS: bool = False

    HTTPX_PROXY: SecretStr | None = None

    @property
    def base_url(self) -> URL:
        return URL(f"https://{self.DOMAIN}")

    @property
    def frontend_url(self) -> URL:
        return self.base_url / "web-app"

    @property
    def base_api_url(self) -> URL:
        return self.base_url / "backend" / "api"

    @property
    def v1_api_url(self) -> URL:
        return self.base_api_url / "v1"

    @property
    def processing_api_url(self) -> URL:
        return self.base_api_url / "processing"


core_settings = CoreSettings()
