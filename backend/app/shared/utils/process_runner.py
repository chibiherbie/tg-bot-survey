import asyncio
import atexit
import signal
from contextlib import suppress
from multiprocessing import Process
from typing import Any, TypeVar

from core.logs import logger
from dto.base import BaseDTO
from interactors.base import BaseInteractor

T = TypeVar("T", bound=BaseInteractor)
D = TypeVar("D", bound=BaseDTO)

# Constants for timeouts
DEFAULT_SHUTDOWN_TIMEOUT = 5.0
FORCE_KILL_TIMEOUT = 1.0


def _execute_interactor[T](interactor_cls: type[T], dto: D) -> None:
    import asyncio  # noqa: PLC0415

    from di.utils import create_container  # noqa: PLC0415
    from dishka import Scope  # noqa: PLC0415

    async def _inner() -> None:
        container = create_container()
        async with container(scope=Scope.REQUEST) as scoped_container:
            interactor = await scoped_container.get(interactor_cls)
            result = interactor.execute(dto)
            if asyncio.iscoroutine(result):
                await result

    with suppress(Exception):
        asyncio.run(_inner())


class ProcessRunner:
    def __init__(self) -> None:
        self.tasks: set[Process] = set()
        self._shutdown_timeout = DEFAULT_SHUTDOWN_TIMEOUT
        self._registered_signals: dict[int, Any] = {}

        self._register_shutdown_handlers()

    def _register_shutdown_handlers(self) -> None:
        """Register shutdown handlers for graceful termination"""
        atexit.register(self._sync_shutdown)

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                handler = signal.signal(sig, self._signal_handler)
                self._registered_signals[sig] = handler
                logger.info("Registered signal handler for %s", sig)
            except (ValueError, OSError) as e:
                logger.warning(
                    "Failed to register signal handler for %s: %s",
                    sig,
                    e,
                )

    def queue_interactor(self, interactor: type[T], dto: D) -> None:
        """Create and start a new process for the given interactor and DTO"""
        try:
            proc = Process(
                target=_execute_interactor,
                args=(interactor, dto),
                daemon=True,
            )
            proc.start()
            self.tasks.add(proc)
            asyncio.create_task(self._wait(proc))  # noqa: RUF006
        except Exception as e:
            logger.exception("Failed to create process: %s", exc_info=e)
            raise

    async def _wait(self, proc: Process) -> None:
        """Wait for process completion and cleanup"""
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, proc.join)
            if proc.exitcode not in (0, None):
                logger.error(
                    "Process %s exited with code %s",
                    proc.pid,
                    proc.exitcode,
                )
        except Exception as e:  # noqa: BLE001
            logger.exception(
                "Error waiting for process %s: %s",
                proc.pid,
                exc_info=e,
            )
        finally:
            self.tasks.discard(proc)

    def _terminate_process(self, proc: Process, timeout: float) -> bool:
        """Terminate a single process with timeout.
        Returns True if process was terminated."""
        if not proc.is_alive():
            return True

        try:
            logger.info("Terminating process %s", proc.pid)
            proc.terminate()
            proc.join(timeout)

            if proc.is_alive():
                logger.warning(
                    "Process %s still alive after terminate, killing",
                    proc.pid,
                )
                proc.kill()
                proc.join(FORCE_KILL_TIMEOUT)

            return not proc.is_alive()
        except Exception as e:  # noqa: BLE001
            logger.exception(
                "Error terminating process %s: %s",
                proc.pid,
                exc_info=e,
            )
            return False

    async def shutdown(self) -> None:
        if not self.tasks:
            return

        logger.info("Shutting down %d processes", len(self.tasks))

        loop = asyncio.get_running_loop()
        results = await asyncio.gather(
            *[
                loop.run_in_executor(
                    None,
                    self._terminate_process,
                    proc,
                    self._shutdown_timeout,
                )
                for proc in list(self.tasks)
            ],
            return_exceptions=True,
        )

        failed_count = sum(1 for result in results if result is not True)
        if failed_count:
            logger.error("Failed to terminate %d processes", failed_count)

        self.tasks.clear()

    def _signal_handler(self, signal_num: int, *_) -> None:
        logger.info(
            "Received signal %s, shutting down ProcessRunner",
            signal_num,
        )
        self._sync_shutdown()

        # Re-raise signal with original handler if needed
        if signal_num in self._registered_signals:
            signal.signal(signal_num, self._registered_signals[signal_num])
            signal.raise_signal(signal_num)

    def _sync_shutdown(self) -> None:
        for proc in list(self.tasks):
            self._terminate_process(proc, self._shutdown_timeout)
        self.tasks.clear()
