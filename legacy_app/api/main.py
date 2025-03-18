from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import settings
from .middlewares import CacheControlMiddleware
from . import passes
from . import satellites
from . import locations
from . import v1


description = """
The Pass Predict API allows you to search for predicted satellite overpasses of a location on Earth.

Base URL: `https://passpredict.com/api`

Please note: This website and API are in active development and the endpoints are subject to change without notice.
"""

origins = ["*"] if settings.DEBUG else ['passpredict.com', 'www.passpredict.com']


def create_app(db, cache):
    app = FastAPI(
        title="Pass Predict API",
        description=description,
        version="0.1.0",
        debug=settings.DEBUG
    )
    app.state.db = db
    app.state.cache = cache
    v1.app.state.db = db
    v1.app.state.cache = cache

    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_headers=['*'],
        expose_headers=['Cache-Control'],
    )
    app.add_middleware(CacheControlMiddleware)

    # Add Public API Version 1 application
    app.mount("/v1", v1.app)

    # Add routes
    app.include_router(
        passes.router,
        prefix='/passes',
    )
    app.include_router(
        satellites.router,
        prefix='/satellites',
    )
    app.include_router(
        locations.router,
        prefix='/locations',
    )

    return app