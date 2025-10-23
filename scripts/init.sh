#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_TEMPLATE="${ROOT_DIR}/.env.example"
ENV_FILE="${ROOT_DIR}/.env"

if [[ ! -f "${ENV_TEMPLATE}" ]]; then
  echo "[WARN] Не найден файл шаблона ${ENV_TEMPLATE}" >&2
  exit 1
fi

if [[ -f "${ENV_FILE}" ]]; then
  echo "[INFO] Файл ${ENV_FILE} уже существует. Пропускаю создание."
else
  cp "${ENV_TEMPLATE}" "${ENV_FILE}"
  echo "[OK] Создан файл ${ENV_FILE} на основе ${ENV_TEMPLATE}"
  echo "   Отредактируйте его перед запуском проекта."
fi
