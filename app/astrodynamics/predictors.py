from orbit_predictor.predictors.accurate import HighAccuracyTLEPredictor


class SatellitePredictor(HighAccuracyTLEPredictor):
    """
    Predictor for satellite overpasses. Uses sgp4 for propagation
    """
    def __init__(self, satid: int):
        """
        Params:
            satid: int = NORAD id for satellite
            source: PasspredictTLESource
        """
        self.satid = satid
        self._source = None
        self.tle = None
        self._propagator = None

    def set_propagator(self):
        self._propagator = self._get_propagator()