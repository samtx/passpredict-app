from datetime import datetime, timedelta
from collections.abc import Iterable, Iterator, Sequence

from api import astrodynamics as astro
from api.domain import Overpass, Point, Satellite, Location


def compute_passes(
    satellites: Iterable[Satellite],
    location: Location,
    start: datetime,
    end: datetime,
    visible_only: bool = False,
    aos_at_deg: float = 0,
    sunrise_deg: float = -6,
    razel_step: float = 60,
) -> list[Overpass]:
    """Compute overpasses for satellites over location"""
    loc = astro.Location(
        latitude_deg=location.latitude,
        longitude_deg=location.longitude,
        elevation_m=location.height,
        name=location.name,
    )
    overpasses = []
    for satellite in satellites:
        orbit = satellite.orbits[0]
        propagator = astro.SGP4Propagator(orbit=orbit, satellite=satellite)
        observer = astro.Observer(location=loc, satellite=propagator)
        predicted_passes = observer.iter_passes(
            start_date=start,
            limit_date=end,
            visible_only=visible_only,
            aos_at_dg=aos_at_deg,
            sunrise_dg=sunrise_deg,
        )
        for predicted_pass in predicted_passes:
            if razel_step > 0:
                dt_razel = list(
                    gen_razel_steps(
                        observer,
                        predicted_pass.aos.datetime,
                        predicted_pass.los.datetime,
                        razel_step,
                    )
                )
            else:
                dt_razel = []
            overpass = Overpass(
                aos=predicted_pass.aos,
                tca=predicted_pass.tca,
                los=predicted_pass.los,
                dt_razel=dt_razel,
                norad_id=satellite.norad_id,
                type=predicted_pass.type,
                vis_begin=predicted_pass.vis_begin,
                vis_end=predicted_pass.vis_end,
                vis_tca=predicted_pass.vis_tca,
            )
            overpasses.append(overpass)
    return overpasses


def gen_razel_steps(
    observer: astro.Observer,
    start: datetime,
    end: datetime,
    step: float,
) -> Iterator[Sequence[datetime, float, float, float]]:
    delta = timedelta(seconds=step)
    dt = start.replace(microsecond=0)
    while dt <= end:
        razel = observer.razel(dt)
        yield (dt, razel.range, razel.az, razel.el)
        dt += delta
