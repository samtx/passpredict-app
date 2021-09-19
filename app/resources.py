import sqlalchemy
from starlette.templating import Jinja2Templates

from app import settings

try:
    import redis
except ImportError:
    import fakeredis as redis
    # Use an in-memory cache


if not settings.REDIS_URL:
    cache = redis.Redis(host=settings.REDIS_HOST, port=6379)
else:
    cache = redis.Redis.from_url(settings.REDIS_URL)


db = sqlalchemy.create_engine(
    settings.DATABASE_URI,
    connect_args={'check_same_thread': False},
    echo=settings.DB_ECHO,
)


templates = Jinja2Templates(directory='app/templates')

# def get_db():
#     if 'db' not in g:
#         g.db = sqlalchemy.create_engine(
#             database_uri,
#             connect_args={'check_same_thread': False},
#             echo=db_echo,
#         )
#     return g.db


# def close_db(e=None):
#     db = g.pop('db', None)

#     if db is not None:
#         db.close()