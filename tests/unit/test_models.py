# test_models.py
import pytest
import numpy as np

from app import models


# def test_find_overpasses_visible_only(init_find_overpasses):
#     """
#     jd, location, sun, sat are created from fixture
#     """
#     jd, location, sun, sat = init_find_overpasses
#     rho = models.RhoVector(jd, sat, location, sun)
#     overpasses = rho.find_overpasses(visible_only=True)
#     for overpass in overpasses:
#         assert overpass.type == models.PassType.visible


def test_SatPredictModel_slice():
    n = 40
    sat = models.SatPredictData(
        id=25544,
        rECEF=np.linspace(0, n*3, n*3).reshape((3, n)),
        illuminated=np.ones(n, dtype=bool)
    )
    slc = slice(10)
    sat2 = sat[slc]
    assert sat2.id == sat.id
    assert np.array_equal(sat2.rECEF, sat.rECEF[:, slc])
    assert np.array_equal(sat2.illuminated, sat.illuminated[slc])


def test_SatPredictModel_slice_array_view():
    n = 40
    sat = models.SatPredictData(
        id=25544,
        rECEF=np.linspace(0, n*3, n*3).reshape((3, n)),
        illuminated=np.ones(n, dtype=bool)
    )
    slc = slice(10)
    sat2 = sat[slc]
    assert id(sat2.id) == id(sat.id)
    assert np.may_share_memory(sat2.rECEF, sat.rECEF[:, slc])
    assert np.may_share_memory(sat2.rECEF, sat.rECEF)
    assert np.may_share_memory(sat2.illuminated, sat.illuminated[slc])
    assert np.may_share_memory(sat2.illuminated, sat.illuminated)


if __name__ == "__main__":
    pytest.main(['-v', __file__])
