import json
from unittest.mock import AsyncMock

import pytest
from pytest import approx

from app.api.locations import _query_geocoding_api, LocationResult


@pytest.fixture
def locations():
    data = json.loads("""
    {"locations": [
        {"name": "Austin, Texas, United States", "lat": 30.2711, "lon": -97.7437},
        {"name": "Austin County, Texas, United States", "lat": 29.88, "lon": -96.28},
        {"name": "Austin Avenue, West Orange, Texas 77630, United States", "lat": 30.0842556, "lon": -93.7611524},
        {"name": "Austin, Newton, Texas 75966, United States", "lat": 30.8602701, "lon": -93.7618013},
        {"name": "North Austin Street, Jasper, Texas 75951, United States", "lat": 30.9270047, "lon": -93.9991561}
    ]}
    """)
    res = LocationResult(**data)
    return res


@pytest.mark.asyncio
async def test_mapbox_geocoder():
    q = 'Austin, Texas, USA'
    res = await _query_geocoding_api(q)
    austin = res.locations[0]
    assert austin.lat == approx(30.25, abs=0.1)
    assert austin.lon == approx(-97.75, abs=0.1)


@pytest.mark.asyncio
async def test_location_api_json_response(client, mocker, locations):
    # Mock Mapbox api query
    geocodermock = AsyncMock(return_value=locations)
    mocker.patch('app.api.locations._query_geocoding_api', side_effect=geocodermock)
    params = {'q': 'Austin, Texas, USA'}
    response = await client.get('/api/locations/', params=params)
    data = response.json()
    austin = data['locations'][0]
    assert austin['lat'] == approx(30.25, abs=0.1)
    assert austin['lon'] == approx(-97.75, abs=0.1)


@pytest.mark.asyncio
async def test_location_api_cache_control_header_set(client, mocker, locations):
    geocodermock = AsyncMock(return_value=locations)
    mocker.patch('app.api.locations._query_geocoding_api', side_effect=geocodermock)
    params = {'q': 'Austin, Texas, USA'}
    response = await client.get('/api/locations/', params=params)
    assert 'cache-control' in response.headers

# def test_location_api(client):
#     query_str = "austin, texas"
#     response = client.get("/api/locations", params={'q': query_str})
#     assert response.status_code == 200
#     data = response.json()
#     locations = data['locations']
#     austin = locations[0]
#     assert austin['lat'] == approx(30.25, abs=0.1)
#     assert austin['lon'] == approx(-97.75, abs=0.1)
