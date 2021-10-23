import urllib.parse
import pickle

from pydantic import BaseModel, Field
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

from app import settings

origins = ["*"] if settings.DEBUG else ['passpredict.com', 'www.passpredict.com']


app = FastAPI(
    title="Pass Predict Location API",
    version="0.1.0",
    debug=settings.DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_headers=['*'],
)


class Location(BaseModel):
    name: str
    lat: float
    lon: float


class LocationResult(BaseModel):
    locations: list[Location]


@app.get('/', response_model=LocationResult)
async def location(q: str, request: Request):
    """
    Geocode query string to get list of coordinates
    """
    key = f"location:{q}"
    cache = request.app.state.cache
    res = await cache.get(key)
    if not res:
        data = await _query_geocoding_api(q)
        await cache.set(key, pickle.dumps(data), ex=86400 * 30)  # cache for 30 days
    else:
        data = pickle.loads(res)
    return data


class Geocoder:
    params = {
        "access_token":  settings.MAPBOX_SECRET_TOKEN,
        'autocomplete': True,
        'types': [
            "postcode",
            "district",
            "place",
            "locality",
            "neighborhood",
            "address",
        ]
    }
    base_url = "https://api.mapbox.com/geocoding/v5/mapbox.places/"

    def _get_location_from_feature(self, feature: dict) -> Location:
        name = feature.get('place_name')
        lon, lat = feature['center']
        return Location(name=name, lat=lat, lon=lon)

    def _parse_geocoding_results(self, data: dict) -> LocationResult:
        features = data['features']
        locations = [self._get_location_from_feature(f) for f in features]
        return LocationResult(locations=locations)

    async def query(self, q: str) -> LocationResult:
        """  Call mapbox geocoding API  """
        url = urllib.parse.quote(q)
        async with httpx.AsyncClient(base_url=self.base_url, params=self.params) as client:
            res = await client.get(url +'.json')
        if res.status_code == 200:
            data = res.json()
            return self._parse_geocoding_results(data)
        else:
            raise HTTPException(status_code=res.status_code, detail="error in location geocoding API call")


async def _query_geocoding_api(q: str) -> LocationResult:
    """
    Call Mapbox geocoding api and parse results
    """
    geocoder = Geocoder()
    data = await geocoder.query(q)
    return data
