from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import markdown
from starlette import middleware

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_headers=['*'],
)
app.include_router(
    passes.router,
    prefix='/passes',
)


@app.get('/', include_in_schema=False)
def home(request: Request):
    """
    Render API homepage with explanation on how to use the API
    """
    # Get markdown content
    fpath = Path(templates.directory) / 'api-home.md'
    config = {
        'toc': {
            'permalink': True,
            'baselevel': 2,
        }
    }
    with open(fpath, 'r') as f:
        content = markdown.markdown(
            f.read(),
            extensions=['fenced_code', 'toc'],
            extension_configs=config,
        )
    context = {
        'request': request,
        'content': content,
    }
    return templates.TemplateResponse('api-home.html', context)
