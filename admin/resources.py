from redis import Redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import settings

if not settings.REDIS_URL:
    if not settings.REDIS_PASSWORD:
        redis_uri = "redis://{host}:{port}/{db}".format(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
        )
    else:
        redis_uri = "redis://{user}:{password}@{host}:{port}/{db}".format(
            user=settings.REDIS_USER,
            password=settings.REDIS_PASSWORD,
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
        )
else:
    redis_uri = settings.REDIS_URL

cache = Redis.from_url(redis_uri)


if settings.POSTGRES_URI:
    postgres_uri = settings.POSTGRES_URI
else:
    postgres_uri = "postgresql://{user}:{password}@{host}:{port}/{database}".format(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_NAME
    )

