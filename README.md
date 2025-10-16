## Быстрый старт

### 1. Инициализация проекта

Создайте файл `.env` из шаблона:

```bash
make init
```

Скрипт `scripts/init.sh` берёт `.env.example` и создаёт `.env`, если его ещё нет.

### 2. Запуск проекта

```bash
docker-compose up -d
```

### 3. Остановка проекта

```bash
docker-compose down
```

## Структура проекта

```
tg-bot-father/
├── Makefile
├── README.md
├── docker-compose.yml
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── scripts/
│   ├── init.sh
│   └── configure_domain.py
└── backend/
```

## Команды

- `make init` — создание `.env` из шаблона
- `make help` — краткая справка по доступным целям
- `make migrate` — применить миграции (`alembic upgrade head`)
- `make migrate-create NAME=descr` — сгенерировать новую миграцию

По умолчанию команды берут переменные из `.env` в корне. Если файл лежит в другом месте, передайте путь через `ENV_FILE`, например:

```bash
make migrate ENV_FILE=infra/prod.env
```

> ⚠️ Перед запуском `make migrate` убедитесь, что контейнеры подняты (`docker-compose up -d`) — команда выполняется внутри сервиса `backend`.

Команда `make migrate-create` запускается в dev-конфигурации (`docker-compose.dev.yml`), чтобы новые файлы миграций сразу появлялись в рабочей директории.

## Настройка домена и режима работы бота

1. После `make init` поправьте домен и порт через скрипт:
   ```bash
   python scripts/configure_domain.py --domain bot.example.com --port 8080
   ```
   или быстрейшим способом:
   ```bash
   make domain DOMAIN=bot.example.com PORT=8080
   ```
2. Для работы без публичного домена переключитесь на long polling:
   ```bash
   python scripts/configure_domain.py --webhook off
   ```
   Чтобы вернуть вебхук — выполните `--webhook on`.
   Аналог через make:
   ```bash
   make domain WEBHOOK=off
   ```

Скрипт обновляет переменные `DOMAIN`, `BACKEND_PORT` и `TELEGRAM_USE_WEBHOOK` в `.env`. В режиме polling вебхук не используется, поэтому достаточно запустить контейнеры и настроить токен бота.
