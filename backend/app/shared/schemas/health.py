from shared.enums.health import HealthStatus
from shared.schemas.base import ResponseModel


class ServiceHealthStatus(ResponseModel):
    name: str
    status: HealthStatus
    message: str | None


class HealthStatusResponse(ResponseModel):
    database: ServiceHealthStatus
    openai: ServiceHealthStatus
    telegram: ServiceHealthStatus
    frontend: ServiceHealthStatus

    @property
    def services(self) -> list[ServiceHealthStatus]:
        return [
            self.database,
            self.openai,
            self.telegram,
            self.frontend,
        ]

    @property
    def overall(self) -> HealthStatus:
        if self.database.status != HealthStatus.OK:
            return HealthStatus.CRITICAL
        if self.openai.status not in [HealthStatus.OK, HealthStatus.SHUTDOWN]:
            return HealthStatus.DEGRADED
        if self.telegram.status not in [
            HealthStatus.OK,
            HealthStatus.SHUTDOWN,
        ]:
            return HealthStatus.DEGRADED
        if self.frontend.status != HealthStatus.OK:
            return HealthStatus.CRITICAL
        return HealthStatus.OK
