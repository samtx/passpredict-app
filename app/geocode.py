from typing import Dict

import requests
import aiohttp

from app.settings import HERE_API_KEY
from app.schemas import LocationResult


HERE_URL_BASE = 'https://geocode.search.hereapi.com/v1/geocode'


async def geocode_api(q: str) -> LocationResult:
    """
    Use HERE api for geocoding, asynchronously
    """
    params = {'q': q, 'limit': 1, 'apikey': HERE_API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(HERE_URL_BASE, params=params) as resp:
            if resp.status == 200:
                # do some error checking here
                pass
            json_response = await resp.json()
            data = json_response['items'][0]
            position = data.get('position')
            location = LocationResult(
                name=data.get('title'),
                lat=round(position.get('lat'), 4),
                lon=round(position.get('lng'), 4)
            )
            return location
            


def geocode(q: str) -> LocationResult:
    """
    Query geocoder api or cache to get latitude and longitude for location query
    """

    # first, check redis cache for result

    # second, check database for result

    # finally, send query to HERE geocoding api

    here_url_base = 'https://geocode.search.hereapi.com/v1/geocode'
    params = {
        'q': q,
        'limit': 1,
        'apikey': HERE_API_KEY,
    }
    r = requests.get(here_url_base, params).json()['items'][0]
    position = r.get('position')
    loc = LocationResult(
        name=r.get('title'),
        lat=round(position.get('lat'), 4),
        lon=round(position.get('lng'), 4)
    )
    return loc