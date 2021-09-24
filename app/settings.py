import os

from starlette.config import Config
from starlette.datastructures import URL, Secret, CommaSeparatedStrings


config = Config(".env")

DEBUG = config('PASSPREDICT_DEBUG', cast=bool, default=False)

POSTGRES_URI = config('POSTGRES_URI', cast=URL, default=None)
# Echo sqlalchemy commands to stdout, default false
DB_ECHO = config('DB_ECHO', cast=bool, default=False)
POSTGRES_HOST = config('POSTGRES_HOST', default='localhost')
POSTGRES_PORT = config('POSTGRES_PORT', cast=int, default=5432)
POSTGRES_USER = config('POSTGRES_USER')
POSTGRES_PASSWORD = config('POSTGRES_PASSWORD')
POSTGRES_NAME = config('POSTGRES_NAME', default='passpredict')

HERE_API_KEY = config('HERE_API_KEY', cast=Secret)

# Maximum number of days to predict overpasses for a single satellite
MAX_DAYS = config('MAX_DAYS', cast=int, default=10)

# Time steps for primary sun and satellite position computation
DT_SECONDS = config('DT_SECONDS', cast=int, default=1)

REDIS_HOST = config('REDIS_HOST', default='localhost')
REDIS_PORT = config('REDIS_PORT', cast=int, default=6379)
REDIS_USER = config('REDIS_USER', default='')
REDIS_PASSWORD = config('REDIS_PASSWORD', cast=Secret, default=None)
REDIS_DB = config('REDIS_DB', cast=int, default=0)
REDIS_URL = config('REDIS_URL', cast=URL, default=None)

CORS_ORIGINS = config('CORS_ORIGINS', cast=CommaSeparatedStrings, default='*')



