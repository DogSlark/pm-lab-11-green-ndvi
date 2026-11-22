"""One request per second, serial; cached OSM administrative boundaries."""

import json
import time
from pathlib import Path

import geopandas as gpd
import requests
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
NAMES = [
    "Авиастроительный",
    "Вахитовский",
    "Кировский",
    "Московский",
    "Ново-Савиновский",
    "Приволжский",
    "Советский",
]


def collect():
    folder = ROOT / "data/provenance"
    folder.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in ["Казань"] + [f"{x} район, Казань" for x in NAMES]:
        cache = folder / ("boundary-" + name.replace(", ", "-") + ".json")
        if cache.exists():
            results = json.loads(cache.read_text(encoding="utf-8"))
        else:
            time.sleep(1.1)
            response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": name, "format": "jsonv2", "polygon_geojson": 1, "limit": 5},
                headers={"User-Agent": "GreenNDVI-UniversityResearch/1.0"},
                timeout=60,
            )
            response.raise_for_status()
            results = response.json()
            cache.write_text(json.dumps(results, ensure_ascii=False), encoding="utf-8")
        candidates = [
            x
            for x in results
            if x.get("geojson", {}).get("type") in ["Polygon", "MultiPolygon"] and x["osm_type"] == "relation"
        ]
        if not candidates:
            raise RuntimeError(f"No polygon for {name}")
        item = candidates[0]
        rows.append(
            {"osm_id": item["osm_id"], "name": name.split(",")[0], "geometry": shape(item["geojson"])}
        )
        print(name, item["osm_id"], flush=True)
    frame = gpd.GeoDataFrame(rows, crs=4326)
    out = ROOT / "data/processed"
    out.mkdir(parents=True, exist_ok=True)
    frame.iloc[:1].to_file(out / "boundary.gpkg", driver="GPKG")
    frame.iloc[1:].to_file(out / "districts.gpkg", driver="GPKG")


if __name__ == "__main__":
    collect()
