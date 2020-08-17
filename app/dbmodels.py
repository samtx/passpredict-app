# Database models

import sqlalchemy as sa
from sqlalchemy.orm import relationship #as sa.orm 
import numpy as np

from database import Base, engine

class Satellite(Base):
    __tablename__ = 'satellites'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100))

    tles = sa.orm.relationship('tle')

    def __repr__(self):
        return f"<Satellite(id={self.id}, name={self.name})>"


class Location(Base):
    __tablename__ = 'locations'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.UnicodeText(), index=True, unique=True, nullable=False)
    latitude = sa.Column(sa.Float, nullable=False)
    longitude = sa.Column(sa.Float, nullable=False)
    height = sa.Column(sa.Float)

    def __repr__(self):
        return f'<Location(id={self.id}, name={self.name}, latitude={self.latitude}, longitude={self.longitude}, height={self.height})>'


class Tle(Base):
    __tablename__ = 'tles'

    id = sa.Column(sa.Integer, primary_key=True)
    tle1 = sa.Column(sa.String(150), nullable=False)
    tle2 = sa.Column(sa.String(150), nullable=False)
    epoch = sa.Column(sa.DateTime, nullable=False)
    created = sa.Column(sa.TIMESTAMP(timezone=False), server_default=sa.func.now(), nullable=False)
    satellite_id = sa.Column(sa.Integer, sa.ForeignKey('satellites.id'), nullable=False)

    satellite = sa.orm.relationship("Satellite", back_populates="tle")

    def __repr__(self):
        return f'<Tle(id={self.id}, tle1={self.tle1}, tle2={self.tle2}, epoch={self.epoch}, created={self.created}, satellite_id={self.satellite_id})>'


# Create tables
Base.metadata.create_all(engine)

# Create db session
session = sa.orm.sessionmaker()
session.configure(bind=engine)
s = session()


def load_satellite_and_tle_data():
    # Import 100 brightest satellites and Starlink satellites from Celestrak
    import requests
    import io
    urls = [
        'https://www.celestrak.com/NORAD/elements/visual.txt',
        'https://www.celestrak.com/NORAD/elements/supplemental/starlink.txt'
    ]
    for url in urls:
        tle_data = parse_tle_data_from_celestrak(url)
        for tle, tle_values in tle_data.iteritems():
            pass

        
            




# Load city location data
def load_city_data():
    import pathlib, csv
    p = pathlib.Path(__file__).parent
    data = read_city_data_from_csv(p / 'data/cities.csv')
    return data
        

def read_city_data_from_csv(fname):
    import csv
    city_data = []
    with open(fname, 'r') as f:
        city_reader = csv.reader(f, delimiter=',')
        next(city_reader) # skip header row
        for city in city_reader:
            city_data.append(
                {
                    'name': city[0].lower(),
                    'latitude': float(city[1]),
                    'longitude': float(city[2])
                }
            )
    return city_data
    

def insert_city_data(data):
    # Insert city data into database
    engine.execute(Location.__table__.insert(), data)
    

try:
    print('done')
    # print(data[:5,:])

except:
    s.rollback()
finally:
    s.close()


def init_database():
    # Create the SQL database if it does not exist
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":

    load_satellite_and_tle_data()

    init_database()
    data = load_city_data()
    insert_city_data(data)
    print(Satellite.__table__)


