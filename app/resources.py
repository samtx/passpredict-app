import sqlalchemy
from flask import current_app, g

from app.settings import database_uri, db_echo, REDIS_HOST, REDIS_URL

try:
    import redis
except ImportError:
    import fakeredis as redis


if not REDIS_URL:
    cache = redis.Redis(host=REDIS_HOST, port=6379)
else:
    cache = redis.Redis.from_url(REDIS_URL)


db = sqlalchemy.create_engine(
    database_uri,
    connect_args={'check_same_thread': False},
    echo=db_echo,
)

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