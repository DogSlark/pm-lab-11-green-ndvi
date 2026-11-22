import numpy as np
import pytest

from ndvi import clear_land, ndvi, priority_mask, temperature_c


def test_scaled_ndvi_uses_additive_offset():
    # DN 20000 -> reflectance .35; DN 30000 -> .625
    assert ndvi([20000], [30000])[0] == pytest.approx((0.625 - 0.35) / (0.625 + 0.35))


def test_missing_and_zero_denominator_are_nan():
    assert np.isnan(ndvi([0, 1], [30000, 1])).all()


def test_temperature_usgs_example():
    assert temperature_c([44947])[0] == pytest.approx(29.47974494, abs=0.00001)
    assert np.isnan(temperature_c([0])[0])


def test_qa_cloud_water_and_saturation_excluded():
    flags = np.array([0, 1, 2, 4, 8, 16, 32, 64, 128, 0], dtype="uint16")
    sat = np.array([0] * 9 + [1])
    assert clear_land(flags, sat).tolist() == [
        True,
        False,
        False,
        False,
        False,
        False,
        False,
        True,
        False,
        False,
    ]


def test_priority_boundaries_and_nodata():
    result = priority_mask(np.array([0.29, 0.3, 0.1, np.nan]), np.array([30, 40, 29, 50]), 30)
    assert result.tolist() == [True, False, False, False]


def test_invalid_threshold_rejected():
    with pytest.raises(ValueError):
        priority_mask(np.array([0.1]), np.array([30]), np.nan)
