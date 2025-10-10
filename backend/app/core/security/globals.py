from datetime import timedelta

WEBAPP_SESSION_EXPIRE_IN = timedelta(days=1)
TOKEN_EXPIRE_IN = timedelta(days=1)
HEADER_TOKEN_KEY = "Access-Token"  # noqa: S105
TELEGRAM_WEBHOOK_SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"  # noqa: S105
