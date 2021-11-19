from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView as BaseSqlaModelView
from flask_admin.contrib import rediscli
from redis import Redis

import models
from resources import postgres_uri, redis_uri
import settings

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = postgres_uri
app.config['SECRET_KEY'] = settings.SECRET_KEY
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


class ModelView(BaseSqlaModelView):
    column_display_pk = True


class SatelliteModelView(ModelView):
    can_delete = True
    page_size = 25  # the number of entries to display on the list view
    # inline_models = (models.Tle,)


class TleModelView(ModelView):
    page_size = 25


class UserModelView(ModelView):
    pass


admin = Admin(app, name='Pass Predict Admin', url="/", template_mode='bootstrap3')
app.config['FLASK_ADMIN_SWATCH'] = 'cosmo'   # set optional bootswatch theme

# Add administrative views here
admin.add_view(SatelliteModelView(models.Satellite, db.session, name='Satellite', category='Satellite'))
admin.add_view(ModelView(models.SatelliteStatus, db.session, name='SatelliteStatus', category='Satellite'))
admin.add_view(ModelView(models.SatelliteType, db.session, name='SatelliteType', category='Satellite'))
admin.add_view(ModelView(models.SatelliteOwner, db.session, name='SatelliteOwner', category='Satellite'))
admin.add_view(ModelView(models.LaunchSite, db.session, name='LaunchSite', category='Satellite'))
admin.add_view(TleModelView(models.Tle, db.session, name='TLE'))
admin.add_view(rediscli.RedisCli(Redis.from_url(redis_uri)))