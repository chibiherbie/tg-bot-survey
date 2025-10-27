from dishka import Provider, Scope
from services.app_settings import AppSettingsService
from services.checklist import ChecklistFlowService
from services.email import EmailService
from services.employee_import import EmployeeImportService
from services.health import HealthCheckService
from services.position_change import PositionChangeRequestService
from services.referral_system import ReferralSystemService
from services.telegram import TelegramService
from services.telegram_auth import TelegramAuthService
from services.user import UserService

service_provider = Provider(scope=Scope.REQUEST)
service_provider.provide_all(
    UserService,
    TelegramService,
    TelegramAuthService,
    HealthCheckService,
    ReferralSystemService,
    ChecklistFlowService,
    EmployeeImportService,
    AppSettingsService,
    EmailService,
    PositionChangeRequestService,
)
