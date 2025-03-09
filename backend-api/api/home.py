from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.concurrency import run_in_threadpool
import markdown

from api.settings import config
from api.utils import cache_page


templates = Jinja2Templates(directory=config.template_dir)


@cache_page
async def home_page(request: Request):
    """ Render API homepage with explanation on how to use the API"""
    response = await run_in_threadpool(render_home_html, request)
    return response


def render_home_html(request: Request) -> HTMLResponse:
    fpath = config.static_dir / 'home.md'
    with open(fpath, 'r') as f:
        content = markdown.markdown(
            f.read(),
            extensions=['fenced_code', 'toc'],
            extension_configs={
                'toc': {
                    'permalink': True,
                    'baselevel': 2,
                }
            },
        )
    context = {
        'request': request,
        'content': content,
    }
    return templates.TemplateResponse('home.html', context)
