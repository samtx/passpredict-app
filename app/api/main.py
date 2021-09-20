from fastapi import FastAPI

from app import settings
from . import passes


app = FastAPI(debug=settings.DEBUG)
app.include_router(passes.router)
