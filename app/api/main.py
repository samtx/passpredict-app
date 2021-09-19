from fastapi import FastAPI

from . import passes


app = FastAPI()
app.include_router(passes.router)
