from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from resources import postgres_uri

Base = automap_base()

engine = create_engine(postgres_uri)

# reflect the tables
Base.prepare(engine, reflect=True)

# mapped classes are now created with names by default
# matching that of the table name.
Satellite = Base.classes.satellite
Tle = Base.classes.tle