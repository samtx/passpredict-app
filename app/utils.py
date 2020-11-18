import logging
import datetime
from itertools import zip_longest
from typing import Dict
from pathlib import Path

import requests

from .dbmodels import location, satellite


logger = logging.getLogger(__name__)


def shift_angle(x: float) -> float:
    """Shift angle in radians to [-pi, pi)
    
    Args:
        x: float, angle in radians

    Reference: 
        https://stackoverflow.com/questions/15927755/opposite-of-numpy-unwrap/32266181#32266181
    """
    return (x + np.pi) % (2 * np.pi) - np.pi


def grouper(iterable, n, fillvalue=None):
    """
    from itertools recipes https://docs.python.org/3.7/library/itertools.html#itertools-recipes
    Collect data into fixed-length chunks or blocks
    """
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def get_visible_satellites():
    """
    Download the latest TLEs from celestrak's visible.txt file
    """
    # Read satellite IDs from visible.txt file
    p = Path(__file__).parent / 'visible.txt'
    with open(p, 'r') as f:
        sat_id_strings = f.readlines()
        print(f'{len(sat_id_strings)} visible satellites found')
        visible_sat_ids = [int(sat) for sat in sat_id_strings]
    return visible_sat_ids


    # visible_sat_url = 'https://celestrak.com/NORAD/elements/visual.txt'
    # r = requests.get(visible_sat_url)
    # tle_data = {}
    # for tle_strings in grouper(r.text.splitlines(), 3):
    #     tle_data.update(parse_tle(tle_strings))
    # return tle_data


def parse_tle(tle_string_list):
    """
    Parse a single 3-line TLE from celestrak
    """
    tle0, tle1, tle2 = tle_string_list
    name = tle0.strip()  # satellite name
    satellite_id = satid_from_tle(tle1)
    return {satellite_id : {'name': name, 'tle1': tle1, 'tle2': tle2}}


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


def download_orbit_type_data():
    """
    Populate orbit type category table from JSR.

    Ref: https://www.geeksforgeeks.org/convert-html-table-into-csv-file-in-python/

    orbit_type = Table(
    'orbit_type', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(75)),      # eg. low earth orbit, geostationary orbit
    Column('short_name', String(6)), # eg. LEO, GEO
    Column('description', Text)      # eg. period < 2hr, h > 600 km, incl. < 85deg, ecc ~= .5
    )
    """
    import csv, json
    from bs4 import BeautifulSoup
    import requests
    from sqlalchemy.sql import select
    from .dbmodels import orbit_type
    from .database import engine
    # download table from JSR website
    r = requests.get('https://planet4589.org/space/gcat/web/intro/orbits.html')
    soup = BeautifulSoup(r.text, 'html.parser')
    data = []
    rows = soup.find("table").find_all("tr")[1:]
    for row in rows:
        # remove trailing </td> and split by <td>
        tmp = row.decode_contents().replace('</td>', '').split('<td>')[1:]
        items = [item.strip() for item in tmp]
        desc_array = []
        if items[2]:
            desc_array.append("period " + items[2].lower())
        if items[3]:
            desc_array.append("height " + items[3].lower())
        if len(items)==5 and items[4]:
            desc_array.append("inclination " + items[4].lower())
        if len(items)==6 and items[5]:
            desc_array.append("eccentricity " + items[5].lower())
        
        data.append(
            {
                'short_name': items[0].strip(),
                'name': items[1].strip(),
                'description' : ", ".join(desc_array)
            }
        )
    with open('orbit_type.tsv', 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['short_name', 'name', 'description'], delimiter='\t')
        writer.writeheader()
        writer.writerows(data)

def import_orbit_type_data():
    import csv
    from sqlalchemy.sql import select
    from .dbmodels import orbit_type
    from .database import engine
    
    with open('orbit_type.tsv', 'r') as f:
        data = csv.DictReader()
        # json.dump(data, f)
    # with engine.connect() as conn:
    #     for d in data:
    #         conn.execute(orbit_type.insert(), d)
    #         print(f"Inserted Orbit {d['short_name']}")


# def update_satellite_data():
#     """
#     Update satellite database with dataset from Jonathan's Space Report
#     url = https://planet4589.org/space/gcat/tsv/cat/satcat.tsv
#     """
#     import requests, csv
#     from sqlalchemy.sql import select, insert
#     from .dbmodels import engine, satellite, JSR_status_decayed


def empty_string_to_None(data: Dict) -> Dict:
    """
    Take a dictionary and convert any empty string values to None
    """
    for key, value in data.items():
        if value == "":
            data[key] = None
    return data


def load_initial_satellite_data():
    """
    Download satellite database from Jonathan's Space Report and load non-decayed satellites into database
    """
    import requests, csv
    from sqlalchemy.sql import select, exists, update
    from .dbmodels import satellite, JSR_status_decayed
    from .schemas import Satellite
    from .database import engine
    # r = requests.get('https://planet4589.org/space/gcat/tsv/cat/satcat.tsv')
    with open('satdb.csv', 'r') as f:
        sat_reader = csv.DictReader(f)
        k = 0
        for sat in sat_reader:
            sat = empty_string_to_None(sat) # convert empty string to None
            k += 1
            # if k > 40000: break
            with engine.connect() as conn:
                satid = int(sat['Satcat'])  # NORAD ID
                res = conn.execute(select([exists().where(satellite.c.id == satid)])).first()[0]
                if (not res) and (sat['Status'] not in JSR_status_decayed):
                    # Satellite is not in database and is still in orbit, so add it to database
                    sat_data = Satellite(**{  
                        'id': satid,
                        'cospar_id': sat['COSPAR_ID'],
                        'name': sat['Name'],
                        'decayed': False,
                        'launch_date': datetime.date.fromisoformat(sat['LaunchDate']) if sat['LaunchDate'] is not None else None,
                        'launch_year': sat['LaunchYear'],
                        'mass': sat['Mass'],
                        'length': sat['Length'],
                        'diameter': sat['Diameter'],
                        'span': sat['Span'],
                        'perigee': sat['Perigee'],
                        'apogee': sat['Apogee'],
                        'inclination': sat['Inc']
                    })
                    conn.execute(satellite.insert(), sat_data.dict())
                    msg = f"Added satellite {satid} to database"
                    logger.info(msg)
                    print(msg)
                elif (res) and (sat['Status'] in JSR_status_decayed):
                    # Satellite is in database but is now decayed, so mark it decayed
                    conn.execute(satellite.update().where(satellite.c.id==satid).values(decayed=True))
                    msg = f"Marked satellite {satid} as decayed in database"
                    logger.info(msg)
                    print(msg)


def clean_city_data():
    """
    Load world city location data from simplemaps.com, licensed by CC 4.0
    https://simplemaps.com/static/data/world-cities/basic/simplemaps_worldcities_basicv1.6.zip
    """
    import pathlib, csv, zipfile, io
    url = 'https://simplemaps.com/static/data/world-cities/basic/simplemaps_worldcities_basicv1.6.zip'
    r = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extract('worldcities.csv')
    data_dict = {}
    fname = pathlib.Path('worldcities.csv')
    with open(fname, 'r') as f:
        city_reader = csv.reader(f, delimiter=',')
        next(city_reader) # skip header row
        for city in city_reader:
            data_dict[city[0].lower()] = {  # Unicode city name
                'lat': float(city[2]),
                'lon': float(city[3])
            }
    data_list = [{
        'query': key,
        'name': key,
        'lat': data_dict[key]['lat'],
        'lon': data_dict[key]['lat']
        } for key in data_dict.keys()
    ]
    # write cleaned output to file
    with open('worldcities_cleaned.csv', 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'lat', 'lon'])
        writer.writeheader()
        writer.writerows(data_list)


def load_initial_city_data():
    """
    Load world city location data from simplemaps.com, licensed by CC 4.0
    https://simplemaps.com/static/data/world-cities/basic/simplemaps_worldcities_basicv1.6.zip
    """
    import pathlib, csv, zipfile, io
    from .dbmodels import engine, location
    with open('worldcities_cleaned.csv', 'r') as f:
        city_reader = csv.DictReader(f)
        data = [city for city in city_reader]   
        with engine.connect() as conn:
            conn.execute(location.insert(), data)


def epoch_from_tle_datetime(epoch_string: str) -> datetime:
    """
    Return datetime object from tle epoch string
    """
    epoch_year = int(epoch_string[0:2])
    if epoch_year < 57:
        epoch_year += 2000
    else:
        epoch_year += 1900
    epoch_day = float(epoch_string[2:])
    epoch_day, epoch_day_fraction = divmod(epoch_day, 1)
    epoch_microseconds = epoch_day_fraction * 24 * 60 * 60 * 1e6
    return datetime.datetime(epoch_year, month=1, day=1, tzinfo=datetime.timezone.utc) + \
        datetime.timedelta(days=int(epoch_day-1)) + \
        datetime.timedelta(microseconds=int(epoch_microseconds)
    )
    

def epoch_from_tle(tle1: str) -> datetime:
    """
    Extract epoch as datetime from tle line 1
    """
    epoch_string = tle1[18:32]
    return epoch_from_tle_datetime(epoch_string)
    

def satid_from_tle(tle1: str) -> int:
    """
    Extract satellite NORAD ID as int from tle line 1
    """
    return int(tle1[2:7])
