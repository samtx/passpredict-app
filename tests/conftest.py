# from __future__ import annotations
# from databases.core import Database

# import pytest
# from starlette.testclient import TestClient
# from starlette.config import environ
# import databases
# import alembic

# environ['POSTGRES_NAME'] = 'test'
# environ['REDIS_DB'] = 'test'

# from app.main import app
# from app import settings


# @pytest.fixture(scope='session', autouse=True)
# def create_test_database():
#     """
#     Create a clean database with rollbacks
#     """
#     postgres_test_uri = "postgresql://{user}:{password}@{host}:{port}/{database}".format(
#         host=settings.POSTGRES_HOST,
#         port=settings.POSTGRES_PORT,
#         user=settings.POSTGRES_USER,
#         password=settings.POSTGRES_PASSWORD,
#         database='test'
#     )
#     db = databases.Database(postgres_test_uri, force_rollback=True)
#     db.connect()



# @pytest.fixture()
# def client():
#     """
#     Create test client
#     """