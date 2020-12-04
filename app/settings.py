import os

import dotenv

dotenv.load_dotenv()

database_uri = os.getenv('DATABASE_URI', 'sqlite:///passpredict.sqlite')

# Echo sqlalchemy commands to stdout, default false
db_echo = bool(os.getenv('DB_ECHO', False))

HERE_API_KEY = os.getenv('HERE_API_KEY')

# Maximum number of days to predict overpasses for a single satellite
MAX_DAYS = int(os.getenv('MAX_DAYS', 10))

# Time steps for primary sun and satellite position computation
DT_SECONDS = int(os.getenv('DT_SECONDS', 1))

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')

cors_origins_string = os.getenv('CORS_ORIGINS', '*')
CORS_ORIGINS = cors_origins_string.split(',')



