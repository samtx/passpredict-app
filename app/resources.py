from aioredis import Redis
from databases import Database
from starlette.staticfiles import StaticFiles

from app import settings
from app.templating import Jinja2Templates


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

db = Database(postgres_uri)

if settings.DEBUG:
    mapbox_client_token = settings.MAPBOX_DEFAULT_TOKEN
else:
    mapbox_client_token = settings.MAPBOX_ACCESS_TOKEN

mapbox_server_token = settings.MAPBOX_SECRET_TOKEN

templates = Jinja2Templates(directory='app/templates')
# Create custom datetime format Jinja filter
datetime_format = lambda v, f="%H:%M %d-%m-%y" :  v.strftime(f)
templates.env.filters["strftime"] = datetime_format
# Add python zip() builtin function to Jinja templates
templates.env.globals['zip'] = zip

static_app = StaticFiles(directory='static')
