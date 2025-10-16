from dishka import Provider, Scope
from services.health import HealthCheckService
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
)
