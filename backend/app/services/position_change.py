from __future__ import annotations

from core.logs import logger
from entities.checklist.models import Employee
from entities.user.models import User
from services.app_settings import AppSettingsService
from services.email import EmailService

POSITION_CHANGE_SETTINGS_KEY = "position_change_notification"


class PositionChangeRequestService:
    def __init__(
        self,
        settings_service: AppSettingsService,
        email_service: EmailService,
    ) -> None:
        self.settings_service = settings_service
        self.email_service = email_service

    async def send_request(self, user: User, employee: Employee) -> bool:
        config = await self.settings_service.get_json(
            POSITION_CHANGE_SETTINGS_KEY,
        )
        if not config:
            logger.warning("Position change notification config missing")
            return False

        try:
            smtp_host = config["smtp_host"]
            smtp_port = int(config.get("smtp_port", 587))
            use_tls = bool(config.get("use_tls", True))
            from_email = config["from_email"]
            to_emails = config.get("to_emails") or []
            subject = config.get(
                "subject",
                "Запрос на обновление должности",
            )
        except KeyError as exc:
            logger.warning(
                "Incomplete position change config",
                missing=str(exc),
            )
            return False

        if not to_emails:
            logger.warning("Position change notification recipients missing")
            return False

        body = self._build_body(user, employee)

        try:
            await self.email_service.send_email(
                host=smtp_host,
                port=smtp_port,
                username=config.get("username"),
                password=config.get("password"),
                use_tls=use_tls,
                from_email=from_email,
                to_emails=to_emails,
                subject=subject,
                body=body,
            )
        except Exception:
            return False
        return True

    @staticmethod
    def _build_body(user: User, employee: Employee) -> str:
        lines = [
            "Запрошено обновление должности",
            "",
            f"Telegram user id: {user.id}",
            f"Telegram username: @{user.tg_username}"
            if user.tg_username
            else "",
            f"Табельный номер: {employee.tab_number}",
            f"Текущая должность: {employee.position.name if employee.position else 'не указана'}",
        ]
        return "\n".join(line for line in lines if line)
