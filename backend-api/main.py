from pprint import pprint

import httpx


def get_satellites():
    params = {
        "search": "starlink",
        "decayed": False,
    }
    with httpx.Client(
        base_url="http://localhost:8000/api",
        timeout=None,
        follow_redirects=True,
    ) as client:
        res = client.get("/v1/satellites", params=params)

    if res.status_code >= 400:
        print(res.status_code, res.text)
        return

    data = res.json()
    pprint(data)


def get_passes():
    params = {
        "norad_id": [25544],
        "latitude": 32.1234498456,
        "longitude": -110.5478,
        "days": 1,
    }
    with httpx.Client(
        base_url="http://localhost:8000/api",
        timeout=None,
        follow_redirects=True,
    ) as client:
        res = client.get("/v1/passes", params=params)

    if res.status_code >= 400:
        print(res.status_code, res.text)
        return

    data = res.json()
    pprint(data)


if __name__ == "__main__":
    # get_passes()
    get_satellites()
