"""Landsat Collection 2 calculations, with explicit missing-data handling."""

import numpy as np


def clear_land(qa, saturation):
    """Exclude fill, dilated cloud, cirrus, cloud, shadow, snow, water, saturation."""
    return ((qa.astype("uint16") & 0b10111111) == 0) & (saturation == 0)


def ndvi(red_dn, nir_dn):
    red = np.asarray(red_dn, dtype=float) * 0.0000275 - 0.2
    nir = np.asarray(nir_dn, dtype=float) * 0.0000275 - 0.2
    valid = (np.asarray(red_dn) != 0) & (np.asarray(nir_dn) != 0)
    valid &= (red >= 0) & (nir >= 0) & ((nir + red) > 0)
    result = np.full(red.shape, np.nan)
    np.divide(nir - red, nir + red, out=result, where=valid)
    return result


def temperature_c(dn):
    values = np.asarray(dn, dtype=float)
    return np.where(values > 0, values * 0.00341802 + 149.0 - 273.15, np.nan)


def priority_mask(vegetation, temperature, threshold_c, ndvi_limit=0.3):
    if not np.isfinite(threshold_c):
        raise ValueError("Temperature threshold must be finite")
    return (
        np.isfinite(vegetation)
        & np.isfinite(temperature)
        & (vegetation < ndvi_limit)
        & (temperature >= threshold_c)
    )
