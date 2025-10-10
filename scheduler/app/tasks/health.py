import core.globals as gl


async def processing_health_check():
    client = gl.processing_client
    if client is None:
        raise RuntimeError()
    await client.health_check()
