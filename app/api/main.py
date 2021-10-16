from fastapi import FastAPI, Request

from app import settings
from app.resources import templates
from . import passes


description = """
The Pass Predict API allows you to search for predicted satellite overpasses of a location on Earth.

Base URL: `https://passpredict.com/api`

Please note: This website and API are in active development and the endpoints are subject to change without notice.
"""


app = FastAPI(
    title="Pass Predict API",
    description=description,
    version="0.1.0",
    # contact={
    #     "name": "Sam Friedman",
    #     "url": "https://passpredict.com/api/contact",
    # },
    debug=settings.DEBUG
)
app.include_router(passes.router)


@app.get('/', include_in_schema=False)
def home(request: Request):
    """
    Render API homepage with explanation on how to use the API
    """
    context = {
        'request': request,
    }
    return templates.TemplateResponse('api-home.html', context)
