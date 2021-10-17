from starlette.templating import Jinja2Templates as StarletteJinja2Templates


class Jinja2Templates(StarletteJinja2Templates):

    @property
    def directory(self):
        return self.env.loader.searchpath[0]
