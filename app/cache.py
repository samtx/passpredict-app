from __future__ import annotations

try:
    import redis
except ImportError:
    import fakeredis as redis

from app.settings import REDIS_HOST, REDIS_URL

if not REDIS_URL:
    cache = redis.Redis(host=REDIS_HOST, port=6379)
else:
    cache = redis.Redis.from_url(REDIS_URL)