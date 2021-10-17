The prediction algorithm is available as a CORS-enabled developer API.
Full OpenAPI documentation can be found at [passpredict.com/api/docs](/api/docs).

Base URL: `https://passpredict.com/api`

Endpoints:

[TOC]

## `GET /passes/`

Parameters:

- `satid` int (required). Norad satellite ID number.
- `lat` float (required). Location latitude in degrees from North. Max precision 4 decimal points
- `lon` float (required). Location longitude in degrees from East. Max precision 4 decimal points
- `h` float. Locaiton height above WGS84 ellipsoid in meters. Default 0.
- `days` int, between 1 and 10. Default 10

Example request:
```
GET /api/passes/?satid=25544&lat=38.32&lon=-97.4 HTTP/1.1
Accept: */*
Accept-Encoding: gzip, deflate
Connection: keep-alive
Host: passpredict.com
User-Agent: HTTPie/2.6.0
```

Response:
```json
{
    "location": {
        "h": 0.0,
        "lat": 38.32,
        "lon": -97.4,
        "name": ""
    },
     "satellite": {
        "id": 25544,
        "name": "International Space Station"
    },
    "overpasses": [
        {
            "aos": {
                "az": 217.46,
                "az_ord": "SW",
                "datetime": "2021-10-17T08:28:27.777801-05:00",
                "el": 10.07,
                "range": 1491.104,
                "timestamp": 1634477307.777801
            },
            "duration": 396.4,
            "los": {
                "az": 57.67,
                "az_ord": "ENE",
                "datetime": "2021-10-17T08:35:04.222335-05:00",
                "el": 10.08,
                "range": 1495.997,
                "timestamp": 1634477704.222335
            },
            "max_elevation": 58.97,
            "satid": 25544,
            "tca": {
                "az": 138.57,
                "az_ord": "SE",
                "datetime": "2021-10-17T08:31:45.073797-05:00",
                "el": 58.97,
                "range": 487.257,
                "timestamp": 1634477505.073797
            }
        },...
    ]
}
```


## `GET /passes/detail/`

Parameters:

- `satid` int (required). Norad satellite ID number.
- `aosdt` datetime (required). Datetime in isoformat for start of pass.
- `lat` float (required). Location latitude in degrees from North. Max precision 4 decimal points
- `lon` float (required). Location longitude in degrees from East. Max precision 4 decimal points
- `h` float. Location height above WGS84 ellipsoid in meters. Default 0.

Example request:
```
GET /api/passes/detail/?satid=25544&aosdt=2021-10-16T15%3A00%3A00.000000-05%3A00&lat=38.32&lon=-97.4 HTTP/1.1
Accept: */*
Accept-Encoding: gzip, deflate
Connection: keep-alive
Host: passpredict.com
User-Agent: HTTPie/2.6.0
```

Response:
```json
{
    "location": {
        "h": 0.0,
        "lat": 38.32,
        "lon": -97.4,
        "name": ""
    },
    "overpass": {
        "aos": {
            "az": 42.49,
            "az_ord": "NE",
            "datetime": "2021-10-16T15:52:35.634340-05:00",
            "el": 37.81,
            "range": 1306.969,
            "timestamp": 1634417555.63434
        },
        "duration": 246.4,
        "los": {
            "az": 39.9,
            "az_ord": "NE",
            "datetime": "2021-10-16T15:56:41.989395-05:00",
            "el": 29.29,
            "range": 2106.789,
            "timestamp": 1634417801.989395
        },
        "max_elevation": 37.81,
        "satid": 25544,
        "tca": {
            "az": 41.99,
            "az_ord": "NE",
            "datetime": "2021-10-16T15:54:37.885720-05:00",
            "el": 32.15,
            "range": 1745.451,
            "timestamp": 1634417677.88572
        }
    },
    "satellite": {
        "id": 25544
    }
}
```