#!/usr/bin/env python3
"""CLI helper to import employees from an XLSX file."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Make backend app importable when launched from repo root
ROOT_DIR = Path(__file__).resolve().parents[1]
APP_PATH = ROOT_DIR / "backend" / "app"
if str(APP_PATH) not in sys.path:
    sys.path.insert(0, str(APP_PATH))

from core.config import core_settings  # noqa: E402
from di import container  # noqa: E402
from dishka import Scope  # noqa: E402
from services.employee_import import EmployeeImportService  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import employees from XLSX")
    parser.add_argument(
        "xlsx_path",
        type=Path,
        help="Path to the XLSX file",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional path to column-mapping config (defaults to service config)",
    )
    parser.add_argument(
        "--sheet",
        type=str,
        default=None,
        help="Optional sheet name override",
    )
    return parser.parse_args()


async def async_main() -> None:
    args = parse_args()

    # Provide defaults for settings expected by the container when running from CLI
    os.environ.setdefault("DOMAIN", "localhost")
    os.environ.setdefault("JWT_KEY", "change-me")
    _ = core_settings  # noqa: F841  # trigger settings load with defaults

    async with container(scope=Scope.REQUEST) as request_container:
        importer = await request_container.get(EmployeeImportService)
        stats = await importer.import_from_path(
            args.xlsx_path,
            config_path=args.config,
            sheet_name=args.sheet,
        )

    print("Import finished:")
    print(stats.as_message())


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
