from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import markdown
from starlette.background import BackgroundTasks
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
async def home(request: Request):
    """
    Render API homepage with explanation on how to use the API
    """
    # Get markdown content
    key = "markdown:api-home.md"
    cache = request.app.state.cache
    res = await cache.get(key)
    if not res:
        # html is not in cache, re-render it
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
        await cache.set(key, content.encode('utf-8'), ex=86400)  # cache for one day
    else:
        content = res.decode('utf-8')
    context = {
        'request': request,
        'content': content,
    }
    return templates.TemplateResponse('api-home.html', context)


# def render_markdown()