import requests

from passpredict.utils import parse_tle, grouper


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