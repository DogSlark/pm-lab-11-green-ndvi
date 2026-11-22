"""Fail closed on missing or malformed required data products."""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
RULES = json.loads((ROOT / "data/validation.json").read_text(encoding="utf-8"))


def check_layer(name, rule, directory=PROCESSED):
    path = directory / f"{name}.gpkg"
    if not path.exists():
        return [f"missing {name}.gpkg"]
    errors = []
    frame = gpd.read_file(path)
    if frame.crs is None or frame.crs.to_epsg() != 4326:
        errors.append("CRS must be EPSG:4326")
    if len(frame) < rule.get("min_count", 1) or len(frame) > rule.get("max_count", float("inf")):
        errors.append("unexpected feature count")
    if frame.geometry.isna().any() or frame.is_empty.any() or not frame.is_valid.all():
        errors.append("missing, empty or invalid geometry")
    if set(frame.geom_type) - set(rule["geometry"]):
        errors.append("unexpected geometry type")
    for column in rule.get("required", []):
        if column not in frame or frame[column].isna().any():
            errors.append(f"missing/null {column}")
        elif frame[column].astype(str).str.strip().eq("").any():
            errors.append(f"empty {column}")
    keys = rule.get("id", [])
    if keys and all(k in frame for k in keys) and frame.duplicated(keys).any():
        errors.append("duplicate IDs")
    if frame.crs is not None and not frame.empty:
        x0, y0, x1, y1 = frame.to_crs(4326).total_bounds
        b0, b1, b2, b3 = RULES["bbox"]
        if x0 < b0 or y0 < b1 or x1 > b2 or y1 > b3:
            errors.append("outside project bbox")
    if path.stat().st_size > RULES["max_file_mb"] * 1024**2:
        errors.append("file exceeds size limit")
    return errors


def check_rasters():
    errors, grid = [], None
    for name, low, high in [("ndvi", -1, 1), ("temperature", -50, 80)]:
        path = PROCESSED / f"{name}.tif"
        if not path.exists():
            errors.append(f"missing {name}.tif")
            continue
        with rasterio.open(path) as src:
            if src.crs is None or not src.crs.is_projected or src.nodata != -9999:
                errors.append(f"{name}: missing projected CRS or wrong nodata")
            current = (src.crs, src.transform, src.shape)
            if grid is not None and current != grid:
                errors.append("raster grids differ")
            grid = current
            values = src.read(1, masked=True).compressed()
            if not values.size or not np.isfinite(values).all():
                errors.append(f"{name}: empty/non-finite values")
            elif values.min() < low or values.max() > high:
                errors.append(f"{name}: values outside physical QC range")
    return errors


def main():
    failed = []
    for name, rule in RULES["layers"].items():
        errors = check_layer(name, rule)
        print(name + ": " + ("; ".join(errors) if errors else "OK"))
        failed.extend(errors)
    errors = check_rasters()
    print("rasters: " + ("; ".join(errors) if errors else "OK"))
    failed.extend(errors)
    path = PROCESSED / "district_statistics.csv"
    if not path.exists():
        failed.append("missing district_statistics.csv")
    else:
        table = pd.read_csv(path)
        if len(table) != 7 or table.osm_id.nunique() != 7:
            failed.append("district CSV must contain seven unique districts")
        for column in ["valid_fraction", "mean_ndvi", "mean_lst_c", "priority_km2"]:
            if table[column].isna().any() or not np.isfinite(table[column]).all():
                failed.append(f"null/non-finite {column}")
        if not table.valid_fraction.between(0, 1).all():
            failed.append("invalid coverage")
        if not (table.valid_pixels <= table.total_pixels).all():
            failed.append("valid pixels exceed total pixels")
        if not table.mean_ndvi.between(-1, 1).all() or (table.priority_km2 < 0).any():
            failed.append("invalid NDVI or area")
    if failed:
        print("\n".join(failed))
        return 1
    print("All required data products passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
