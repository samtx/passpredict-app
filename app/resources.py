from aioredis import Redis
from databases import Database
from starlette.staticfiles import StaticFiles

from app import settings
from app.templating import Jinja2Templates


def get_redis_uri(config):
    if not config.REDIS_URL:
        if not config.REDIS_PASSWORD:
            redis_uri = "redis://{host}:{port}/{db}".format(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
            )
        else:
            redis_uri = "redis://{user}:{password}@{host}:{port}/{db}".format(
                user=config.REDIS_USER,
                password=config.REDIS_PASSWORD,
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
            )
    else:
        redis_uri = config.REDIS_URL
    return redis_uri


def get_postgres_uri(config):
    if config.POSTGRES_URI:
        postgres_uri = config.POSTGRES_URI
    else:
        postgres_uri = "postgresql://{user}:{password}@{host}:{port}/{database}".format(
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            database=config.POSTGRES_NAME
        )
    return postgres_uri

cache = Redis.from_url(get_redis_uri(settings))

db = Database(get_postgres_uri(settings))

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
