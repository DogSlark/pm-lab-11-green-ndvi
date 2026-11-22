"""Diagnostic PR: the cloud bit must exclude the pixel."""
import numpy as np

from ndvi import clear_land


def test_cloud_pixel_is_excluded():
    result = clear_land(np.array([8], dtype="uint16"), np.array([0]))
    assert bool(result[0]) is False
