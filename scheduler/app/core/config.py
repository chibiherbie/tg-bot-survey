from pydantic import SecretStr
from pydantic_settings import BaseSettings
from yarl import URL


class CoreSettings(BaseSettings):
    PROCESSING_CLIENT_ID: str

    DEBUG: bool = False
    BACKEND_HOST: str = "backend"
    BACKEND_PORT: int = 5000

    DOMAIN: str
    JWT_KEY: SecretStr

    @property
    def base_url(self) -> URL:
        return URL(f"https://{self.DOMAIN}")

    @property
    def base_api_url(self) -> URL:
        return self.base_url / "backend" / "api"

    @property
    def processing_api_url(self) -> URL:
        return self.base_api_url / "processing"


core_settings = CoreSettings()
