import requests

from .dbmodels import location, satellite

from .passpredict.utils import grouper
from .passpredict.tle import parse_tle


def get_visible_satellites():
    """
    Download the latest TLEs from celestrak's visible.txt file
    """
    visible_sat_url = 'https://celestrak.com/NORAD/elements/visual.txt'
    r = requests.get(visible_sat_url)
    tle_data = {}
    for tle_strings in grouper(r.text.splitlines(), 3):
        tle_data.update(parse_tle(tle_strings))
    return tle_data



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

        

def load_city_data():
    """
    Load world city location data from simplemaps.com, licensed by CC 4.0
    """
    import pathlib, csv
    from .database import engine
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
        'name': key,
        'lat': data_dict[key]['lat'],
        'lon': data_dict[key]['lat']
        } for key in data_dict.keys()
    ]
    with engine.connect() as conn:
        conn.execute(location.insert(), data_list)