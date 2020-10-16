import os

import dotenv

dotenv.load_dotenv()

database_uri = 'sqlite:///passpredict.db'

HERE_API_KEY = os.getenv('HERE_API_KEY')
