from collections import namedtuple
import urllib.parse
from dataclasses import dataclass
import asyncio

import pytest
import databases
import aioredis
import httpx
from async_asgi_testclient import TestClient

from app.main import create_app
from app import settings
from app.resources import get_postgres_uri

postgres_uri = get_postgres_uri(settings)


@pytest.fixture(scope='function')
async def client():
    """
    Create async test client
    """
    db = databases.Database(postgres_uri, force_rollback=True)
    redis_url = "redis://{host}:{port}/{db}".format(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB+1,
    )
    cache = aioredis.Redis.from_url(redis_url)
    app = create_app(db=db, cache=cache)
    await db.connect()
    res = await cache.ping()
    assert res
    async with httpx.AsyncClient(app=app, base_url="http://testserver") as _client:
        yield _client
    await cache.flushdb()
    await db.disconnect()
