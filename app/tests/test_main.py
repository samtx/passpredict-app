from fastapi.testclient import TestClient
from pytest_redis import factories

from app.settings import REDIS_HOST
from app.main import app

client = TestClient(app)

redis_noproc = factories.redis_noproc(host=REDIS_HOST, port=6379)
redisdb = factories.redisdb('redis_noproc')

def test_hello_world():
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}


def test_passes_ISS(redisdb):
    satid = 25544  # Int. Space Station
    params = {
        'lat': 32.1234,
        'lon': -97.9876,
        'h': 0.0,
    }
    response = client.get(f"/passes/{satid}", params=params)
    assert response.status_code == 200
    data = response.json()
    assert data.get('location')
    assert data.get('overpasses')
