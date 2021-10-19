import pickle


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

