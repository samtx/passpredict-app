from datetime import date
from fastapi.testclient import TestClient
from pytest_redis import factories

from app import settings
from app.main import app

client = TestClient(app)

# redis_noproc = factories.redis_noproc(host=REDIS_HOST, port=6379)
# redisdb = factories.redisdb('redis_noproc')

class FakeDate(date):
	"""A fake replacement for date that can be mocked for testing.
    Ref: https://williambert.online/2011/07/how-to-unit-testing-in-django-with-mocking-and-patching/
    """
	def __new__(cls, *args, **kwargs):
		return date.__new__(date, *args, **kwargs)


def test_passes_ISS_no_cache(mocker):
    cache_mock = mocker.patch('app.main.cache', spec=True)
    cache_mock.get.return_value = None
    cache_mock.hgetall.return_value = None
    db_mock = mocker.patch('app.main.get_db')
    db_mock.execute.return_value.fetchone.return_value = {
        'tle1': '1 25544U 98067A   20325.70253472 -.00004237  00000-0 -68774-4 0  9996',
        'tle2': '2 25544  51.6469 294.0115 0001421  73.7792 273.6742 15.49017875256278'
    }
    today_mock = mocker.patch('app.main.datetime.date', FakeDate)
    today_mock.today = classmethod(lambda cls: date(2020, 11, 20))
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
    assert len(data.get('overpasses')) > 0


def test_passes_ISS_tle_cache(mocker):
    satid = 25544  # Int. Space Station
    today_mock = mocker.patch('app.main.datetime.date', FakeDate)
    today_mock.today = classmethod(lambda cls: date(2020, 11, 20))
    tle_key = f"tle:{satid}:{date(2020, 11, 20).strftime('%Y%m%d')}"
    tle_values = {
        b'tle1': b'1 25544U 98067A   20325.70253472 -.00004237  00000-0 -68774-4 0  9996',
        b'tle2': b'2 25544  51.6469 294.0115 0001421  73.7792 273.6742 15.49017875256278'
    }
    def cache_mock_hgetall_fn(key):
        if key == tle_key:
            return tle_values
        else:
            return None

    cache_mock = mocker.patch('app.main.cache', spec=True)
    cache_mock.hgetall.side_effect = cache_mock_hgetall_fn
    cache_mock.get.return_value = None
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
    assert len(data.get('overpasses')) > 0
