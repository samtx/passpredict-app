import pytest


@pytest.fixture
def pass_params():
    return {
        'satid': 25544,
        'name': 'Austin, Texas, USA',
        'satname': 'International Space Station',
        'lat': 30.2711,
        'lon': -97.7437,
        'h': 0,
    }


@pytest.mark.asyncio
async def test_api_passes_Austin_ISS(client, pass_params):
    response = await client.get("/api/passes", params=pass_params)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_api_passes_cache_control_header_set(client, pass_params):
    response = await client.get("/api/passes", params=pass_params)
    assert 'cache-control' in response.headers


@pytest.mark.asyncio
async def test_api_passes_json_response(client, pass_params):
    response = await client.get("/api/passes", params=pass_params)
    data = response.json()
    assert 'location' in data
    assert 'satellite' in data
    assert 'overpasses' in data
    assert len(data['overpasses']) > 0
    pass_ = data['overpasses'][0]
    assert 'aos' in pass_
    assert 'los' in pass_
    assert 'tca' in pass_
    assert 'duration' in pass_
    assert 'max_elevation' in pass_
    assert 'type' in pass_
    assert 'satid' in pass_
