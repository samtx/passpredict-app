import os

import dotenv

dotenv.load_dotenv()

database_uri = 'sqlite:///passpredict.db'

HERE_API_KEY = os.getenv('HERE_API_KEY')

# Maximum number of days to predict overpasses for a single satellite
MAX_DAYS = 10

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')



