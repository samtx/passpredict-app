from __future__ import annotations

try:
    import redis
except ImportError:
    import fakeredis as redis

from app.settings import REDIS_HOST

cache = redis.Redis(host=REDIS_HOST, port=6379)