from urllib.parse import urlencode

from aioredis import Redis
from databases import Database
from starlette.templating import Jinja2Templates

from app import settings


if not settings.REDIS_URL:
    cache = Redis(host=settings.REDIS_HOST, port=6379)
else:
    cache = Redis.from_url(settings.REDIS_URL)

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

db = Database(postgres_uri)

templates = Jinja2Templates(directory='app/templates')