from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib import rediscli
from redis import Redis

import models
from resources import postgres_uri, redis_uri

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = postgres_uri
db = SQLAlchemy(app)


@app.after_request
def set_cache_headers(response):
    """ Set Cache-Control headers on static files """

    def _is_cacheable(response):
        if 'javascript' in response.mimetype:
            return True
        if 'css' in response.mimetype:
            return True
        return False

    if _is_cacheable(response):
        response.cache_control.max_age = 86400
        response.cache_control.no_cache = False
    return response


class SatelliteModelView(ModelView):
    column_display_pk = True
    can_delete = True
    page_size = 50  # the number of entries to display on the list view


class UserModelView(ModelView):
    pass


class TleModelView(ModelView):
    page_size = 50


admin = Admin(app, name='Pass Predict Admin', url="/", template_mode='bootstrap3')
app.config['FLASK_ADMIN_SWATCH'] = 'cosmo'   # set optional bootswatch theme

# Add administrative views here
admin.add_view(SatelliteModelView(models.Satellite, db.session, name='Satellite'))
admin.add_view(TleModelView(models.Tle, db.session, name='TLE'))
admin.add_view(rediscli.RedisCli(Redis.from_url(redis_uri)))