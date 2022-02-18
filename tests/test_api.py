import pytest


@pytest.mark.asyncio
async def test_api_passes_cache_control_header_set(client):
    params = {
        'satid': 25544,
        'name': 'Austin, Texas, USA',
        'satname': 'International Space Station',
        'lat': 30.2711,
        'lon': -97.7437,
        'h': 0,
    }
    response = await client.get("/api/passes", params=params, follow_redirects=True)
    assert response.status_code == 200