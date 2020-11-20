from fastapi.testclient import TestClient
from pytest_redis import factories

from app.settings import REDIS_HOST
from app.main import app

client = TestClient(app)

# redis_noproc = factories.redis_noproc(host=REDIS_HOST, port=6379)
# redisdb = factories.redisdb('redis_noproc')

def test_passes_ISS(mocker):
    cache_mock = mocker.patch('app.main.cache', spec=True)  # mock the cache
    cache_mock.get.return_value = None
    db_mock = mocker.patch('app.tle.engine')
    db_mock.connect.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = {
        'tle1': '1 25544U 98067A   20325.70253472 -.00004237  00000-0 -68774-4 0  9996',
        'tle2': '2 25544  51.6469 294.0115 0001421  73.7792 273.6742 15.49017875256278'
    }
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
