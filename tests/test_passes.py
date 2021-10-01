from fastapi.testclient import TestClient

import httpx

from app.main import app

client = TestClient(app)


def test_passes_Austin_ISS():
    params = {
        'satid': 25544,
        'name': 'Austin, Texas, USA',
        'satname': 'International Space Station',
        'lat': 30.2711,
        'lon': -97.7437,
        'h': 0,
    }
    response = client.get("/passes", params=params)
    assert response.status_code == 200


# def test_passes_Austin_ISS_api():
#     params = {
#         'satid': 25544,
#         'name': 'Austin, Texas, USA',
#         'satname': 'International Space Station',
#         'lat': 30.2711,
#         'lon': -97.7437,
#         'h': 0,
#     }
#     response = client.get("/api/passes", params=params)
#     assert response.status_code == 200
