from urllib.parse import quote

import httpx
from starlette.testclient import TestClient

from app import settings
from app.main import app

client = TestClient(app)


def test_mapbox_geocoder():
    """
    Refer to app/static/js/passpredictlib.js for mapbox geocoding API
    """
    query_str = "austin, texas"
    params = {
        'access_token': settings.MAPBOX_ACCESS_TOKEN_DEV,
        'autocomplete': True,
        'types': [
            "postcode",
            "district",
            "place",
            "locality",
            "neighborhood",
            "address",
        ],
    }
    base_url = 'https://api.mapbox.com/geocoding/v5/mapbox.places/'
    url = base_url + f"{quote(query_str)}.json"
    resp = httpx.get(url, params=params)
    assert resp.status_code == 200
    data = resp.json()
    assert 'features' in data
    austin = data['features'][0]
    lon, lat = austin['center']
    assert 30.2 <= lat <= 30.3
    assert -97.7 >= lon >= -97.8


def test_location_api():
    query_str = "austin, texas"
    response = client.get("/locations", params={'q': query_str})
    assert response.status_code == 200
    data = response.json()
    locations = data['locations']
    austin = locations[0]
    assert 30.2 <= austin['lat'] <= 30.3
    assert -97.7 >= austin['lon'] >= -97.8
