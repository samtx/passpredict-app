# TLE source for web app

from orbit_predictor import TLESource


class PasspredictTLESource(TLESource):
    """
    TLE source that checks the redis cache and postgres database
    for orbital elements
    """

    def add_tle(self, sat_id, tle, epoch):
        pass

    def _get_tle(self, sat_id, date):
        pass

