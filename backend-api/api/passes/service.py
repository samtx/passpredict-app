from datetime import datetime, timedelta
from collections.abc import Iterable, Iterator, Sequence
from typing import cast

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
    overpasses = cast(list[Overpass], [])
    it = compute_pass_iterator(
        satellites,
        loc,
        start,
        end,
        visible_only=visible_only,
        aos_at_deg=aos_at_deg,
        sunrise_deg=sunrise_deg,
        razel_step=razel_step,
    )
    overpasses = list(it)
    overpasses.sort(key=lambda op: op.aos.datetime)
    return overpasses


def compute_pass_iterator(
    satellites: Iterable[Satellite],
    location: astro.Location,
    start: datetime,
    end: datetime,
    visible_only: bool,
    aos_at_deg: float,
    sunrise_deg: float,
    razel_step: float,
) -> Iterator[Overpass]:
    for satellite in satellites:
        orbit = satellite.orbits[0]
        propagator = astro.SGP4Propagator(orbit=orbit, satellite=satellite)
        observer = astro.Observer(location=location, satellite=propagator)
        predicted_passes = observer.iter_passes(
            start_date=start,
            limit_date=end,
            visible_only=visible_only,
            aos_at_dg=aos_at_deg,
            sunrise_dg=sunrise_deg,
        )
        for predicted_pass in predicted_passes:
            aos_pt = make_point(predicted_pass.aos)
            los_pt = make_point(predicted_pass.los)
            if razel_step > 0:
                dt_razel = compute_razel_steps(
                    observer,
                    aos_pt.datetime,
                    los_pt.datetime,
                    razel_step,
                )
            else:
                dt_razel = []
            overpass = Overpass(
                aos=aos_pt,
                tca=make_point(predicted_pass.tca),
                los=los_pt,
                dt_razel=dt_razel,
                norad_id=satellite.norad_id,
                type=predicted_pass.type.value.upper(),
                vis_begin=make_point(predicted_pass.vis_begin),
                vis_end=make_point(predicted_pass.vis_end),
                vis_tca=make_point(predicted_pass.vis_tca),
            )
            yield overpass


def compute_razel_steps(
    observer: astro.Observer,
    start: datetime,
    end: datetime,
    step: float,
) -> list[tuple[datetime, float, float, float]]:
    delta = timedelta(seconds=step)
    dt = start.replace(microsecond=0) - delta

    def gen():
        nonlocal dt
        while dt <= end + delta:
            razel = observer.razel(dt)
            yield (dt, razel.range, razel.az, razel.el)
            dt += delta

    return list(gen())


def make_point(pass_point: astro.PassPoint | None) -> Point | None:
    if pass_point is None:
        return None
    return Point(
        datetime=pass_point.dt,
        azimuth=pass_point.azimuth,
        elevation=pass_point.elevation,
        range=pass_point.range,
        brightness=pass_point.brightness,
    )
