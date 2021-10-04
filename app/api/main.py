from fastapi import FastAPI, Request

from app import settings
from app.resources import templates
from . import passes


app = FastAPI(debug=settings.DEBUG)
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
