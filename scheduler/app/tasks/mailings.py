import core.globals as gl


async def process_mailings():
    client = gl.processing_client
    if client is None:
        raise RuntimeError()
    await client.process_mailings()
