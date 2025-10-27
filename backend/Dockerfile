ARG PYTHON_IMAGE_VERSION=3.12.11-alpine3.22

FROM python:$PYTHON_IMAGE_VERSION AS builder

# Установка UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Установка системных зависимостей
RUN apk add --no-cache git gcc musl-dev libffi-dev

# Создание виртуального окружения
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
WORKDIR /app

# Копирование файлов конфигурации
COPY pyproject.toml uv.lock* ./

# Установка зависимостей
RUN uv sync --frozen --no-install-project --no-dev

FROM python:$PYTHON_IMAGE_VERSION AS runtime

# Копирование UV и виртуального окружения
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Создание пользователя для безопасности
RUN addgroup -g 1001 -S app && adduser -u 1001 -S app -G app

# Install curl for healthcheck
RUN apk add --no-cache curl

# Настройка переменных окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PROJECT_DIR=/workspace
ENV PYTHONPATH=$PROJECT_DIR/app
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR $PROJECT_DIR

# Копирование кода приложения
COPY --chown=app:app . .

# Переключение на непривилегированного пользователя
USER app

ENTRYPOINT ["python", "-m", "app"]