from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, MetaData

from resources import postgres_uri

engine = create_engine(postgres_uri)
metadata = MetaData()
metadata.reflect(engine)

Base = automap_base(metadata=metadata)
# reflect the tables
Base.prepare()

# mapped classes are now created with names by default
# matching that of the table name.
Satellite = Base.classes.satellite
Tle = Base.classes.tle
LaunchSite = Base.classes.launch_site
SatelliteOwner = Base.classes.satellite_owner
SatelliteType = Base.classes.satellite_type
SatelliteStatus = Base.classes.satellite_status


def _tle_repr(self):
    """ Define custom repr for TLE object """
    epoch = self.epoch.replace(tzinfo=None)
    return f"({self.id}) Sat {self.satellite_id}, {epoch.isoformat()}"
Tle.__repr__ = _tle_repr


def _name_repr(self):
    """ Define repr to show name of object """
    return f"{self.name}"

LaunchSite.__repr__ = _name_repr
SatelliteOwner.__repr__ = _name_repr
SatelliteType.__repr__ = _name_repr
SatelliteStatus.__repr__ = _name_repr

print('models loaded')