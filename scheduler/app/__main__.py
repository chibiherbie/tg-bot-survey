import asyncio

import core.globals as gl
from aiohttp import ClientSession
from apscheduler import AsyncScheduler
from apscheduler.eventbrokers.redis import RedisEventBroker
from apscheduler.triggers.interval import IntervalTrigger
from clients.backend import ProcessingClient
from db.config import redis_settings
from tasks.health import processing_health_check
from tasks.mailings import process_mailings


async def run():
    """Инициализирует processing_client и запускает планировщик."""
    session = ClientSession()
    try:
        gl.processing_client = ProcessingClient(session)
        event_broker = RedisEventBroker(client_or_url=redis_settings.dsn)
        async with AsyncScheduler(event_broker=event_broker) as scheduler:
            await scheduler.add_schedule(
                processing_health_check,
                IntervalTrigger(minutes=1),
            )
            await scheduler.add_schedule(
                process_mailings,
                IntervalTrigger(minutes=1),
            )
            await scheduler.run_until_stopped()
    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(run())
