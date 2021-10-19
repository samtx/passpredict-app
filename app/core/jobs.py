import pickle
import concurrent.futures
import asyncio

from app.scripts import update_tle_database as update_tle_database_sync


async def set_cache_with_pickle(cache, key, value, ttl=None):
    """
    Add value to cache with ttl. To be used as Background task
    """
    pickled_value = pickle.dumps(value)
    await cache.set(key, pickled_value, ex=ttl)


async def update_tle_database():
    """
    Wrapper for update_tle_database script for arq worker
    """
    executor = concurrent.futures.ProcessPoolExecutor()
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(executor, update_tle_database_sync)

