import importlib.util
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box

spec = importlib.util.spec_from_file_location(
    "validation", Path(__file__).parents[1] / "scripts/validate_data.py"
)
validation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation)
RULE = {"geometry": ["Polygon"], "min_count": 1, "id": ["osm_id"], "required": ["osm_id", "name"]}


def test_missing_layer_fails_closed(tmp_path):
    assert validation.check_layer("districts", RULE, tmp_path)


def test_duplicate_and_null_fields_rejected(tmp_path):
    frame = gpd.GeoDataFrame(
        {"osm_id": [1, 1], "name": ["ok", None]}, geometry=[box(49, 55.7, 49.1, 55.8)] * 2, crs=4326
    )
    frame.to_file(tmp_path / "districts.gpkg", driver="GPKG")
    errors = validation.check_layer("districts", RULE, tmp_path)
    assert "duplicate IDs" in errors
    assert "missing/null name" in errors
