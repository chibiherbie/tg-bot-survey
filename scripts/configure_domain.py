#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Configure DOMAIN and webhook mode in the .env file.",
    )
    parser.add_argument(
        "--domain",
        help="Domain name to set in the .env file (e.g. bot.example.com).",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Backend port exposed inside docker-compose (default from .env).",
    )
    parser.add_argument(
        "--webhook",
        choices={"on", "off", "keep"},
        default="keep",
        help="Enable (on) or disable (off) webhook mode. Default keeps current value.",
    )
    return parser.parse_args()


def ensure_env_file() -> None:
    if ENV_FILE.exists():
        return
    print(
        "[ERR] .env file not found. Run `make init` before configuring the domain.",
        file=sys.stderr,
    )
    sys.exit(1)


def load_lines() -> list[str]:
    return ENV_FILE.read_text(encoding="utf-8").splitlines(keepends=True)


def save_lines(lines: list[str]) -> None:
    # Guarantee trailing newline for POSIX friendliness
    if lines and not lines[-1].endswith("\n"):
        lines[-1] = lines[-1] + "\n"
    ENV_FILE.write_text("".join(lines), encoding="utf-8")


def upsert(lines: list[str], key: str, value: str) -> None:
    prefix = f"{key}="
    for idx, line in enumerate(lines):
        if line.startswith(prefix):
            lines[idx] = f"{prefix}{value}\n"
            return
    if lines and lines[-1] != "\n":
        lines.append("\n")
    lines.append(f"{prefix}{value}\n")


def main() -> None:
    args = parse_args()
    ensure_env_file()
    lines = load_lines()

    if not any([args.domain, args.port, args.webhook != "keep"]):
        print("[INFO] Nothing to update. Provide at least one parameter.")
        return

    if args.domain:
        upsert(lines, "DOMAIN", args.domain)
        print(f"[OK] DOMAIN set to {args.domain}")

    if args.port:
        upsert(lines, "BACKEND_PORT", str(args.port))
        print(f"[OK] BACKEND_PORT set to {args.port}")

    if args.webhook != "keep":
        flag = "true" if args.webhook == "on" else "false"
        upsert(lines, "TELEGRAM_USE_WEBHOOK", flag)
        state = "enabled" if flag == "true" else "disabled"
        print(f"[OK] Webhook mode {state}")

    save_lines(lines)


if __name__ == "__main__":
    main()
