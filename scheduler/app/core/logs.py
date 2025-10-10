import structlog


def register_logger() -> structlog.PrintLogger:
    return structlog.get_logger("backend")


logger = register_logger()
