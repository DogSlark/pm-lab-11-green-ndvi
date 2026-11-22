"""Collect Kazan administrative polygons from OSM Overpass."""

import json
from pathlib import Path

import geopandas as gpd
import requests
from shapely.geometry import LineString, Polygon
from shapely.ops import polygonize, unary_union

ROOT = Path(__file__).resolve().parents[1]
QUERY = """[out:json][timeout:120];
relation["boundary"="administrative"]["name"="Казань"](55.4,48.6,56.2,49.8);
out geom;
relation["boundary"="administrative"]["admin_level"="9"](55.55,48.85,56.0,49.45);
out geom;"""


def relation_polygon(element):
    groups = {}
    for role in ["outer", "inner"]:
        lines = [
            LineString([(p["lon"], p["lat"]) for p in member["geometry"]])
            for member in element.get("members", [])
            if member.get("role") == role and member.get("geometry")
        ]
        groups[role] = unary_union(list(polygonize(unary_union(lines)))) if lines else Polygon()
    return groups["outer"].difference(groups["inner"])


def collect():
    result = None
    for endpoint in [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    ]:
        try:
            response = requests.get(endpoint, params={"data": QUERY}, timeout=180)
            response.raise_for_status()
            result = response.json()
            break
        except requests.RequestException as error:
            print(type(error).__name__, flush=True)
    if result is None:
        raise RuntimeError("All Overpass endpoints failed")
    folder = ROOT / "data/provenance"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "osm-boundaries.json").write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    rows = []
    for element in result["elements"]:
        geometry = relation_polygon(element)
        if not geometry.is_empty:
            rows.append(
                {
                    "osm_id": element["id"],
                    "name": element["tags"].get("name", ""),
                    "admin_level": element["tags"].get("admin_level", ""),
                    "geometry": geometry,
                }
            )
    frame = gpd.GeoDataFrame(rows, crs=4326).drop_duplicates("osm_id")
    out = ROOT / "data/processed"
    out.mkdir(parents=True, exist_ok=True)
    city = frame[frame["name"] == "Казань"]
    if len(city) != 1:
        raise RuntimeError(f"Expected one city polygon, got {len(city)}")
    districts = frame[(frame["name"] != "Казань") & frame.intersects(city.geometry.iloc[0])].copy()
    districts.geometry = districts.geometry.intersection(city.geometry.iloc[0])
    city.to_file(out / "boundary.gpkg", driver="GPKG")
    districts.to_file(out / "districts.gpkg", driver="GPKG")
    print(frame[["osm_id", "name", "admin_level"]].to_string(index=False))


if __name__ == "__main__":
    collect()
