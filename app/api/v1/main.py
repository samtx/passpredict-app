from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app import settings
from app.resources import db, cache
from . import passes


description = """
The Pass Predict API allows you to search for predicted satellite overpasses of a location on Earth.

Base URL: `https://passpredict.com/api/v1`

Please note: This website and API are in active development and the endpoints are subject to change without notice.
"""


app = FastAPI(
    title="Pass Predict Public API",
    description=description,
    version="1.0",
    # contact={
    #     "name": "Sam Friedman",
    #     "url": "https://passpredict.com/api/contact",
    # },
    debug=settings.DEBUG
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_headers=['*'],
    expose_headers=['Cache-Control'],
)

@app.middleware("http")
async def set_cache_control_header(request: Request, call_next):
    """
    Set Cache-Control header for API responses
    """
    response = await call_next(request)
    response.headers['Cache-Control'] = "private, max-age=900"  # cache for 15 minutes
    return response


# Add routes
app.include_router(
    passes.router,
    prefix='/passes',
)