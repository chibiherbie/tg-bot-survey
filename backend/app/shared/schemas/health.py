from shared.enums.health import HealthStatus
from shared.schemas.base import ResponseModel


class ServiceHealthStatus(ResponseModel):
    name: str
    status: HealthStatus
    message: str | None


class HealthStatusResponse(ResponseModel):
    database: ServiceHealthStatus
    telegram: ServiceHealthStatus

    @property
    def services(self) -> list[ServiceHealthStatus]:
        return [
            self.database,
            self.telegram,
        ]

    @property
    def overall(self) -> HealthStatus:
        if self.database.status != HealthStatus.OK:
            return HealthStatus.CRITICAL
        if self.telegram.status not in [
            HealthStatus.OK,
            HealthStatus.SHUTDOWN,
        ]:
            return HealthStatus.DEGRADED
        return HealthStatus.OK
