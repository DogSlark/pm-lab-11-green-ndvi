"""Download real Landsat windows; never store expiring SAS credentials."""

from __future__ import annotations

import json
from pathlib import Path

import rasterio
import requests
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds

ROOT = Path(__file__).resolve().parents[1]
BBOX = (48.85, 55.55, 49.45, 56.0)


def collect(refresh=False):
    raw = ROOT / "data/raw"
    raw.mkdir(parents=True, exist_ok=True)
    bands = ["red", "nir08", "lwir11", "qa_pixel", "qa_radsat"]
    if not refresh and (raw / "scene.json").exists() and all((raw / f"{b}.tif").exists() for b in bands):
        cached = json.loads((raw / "scene.json").read_text(encoding="utf-8"))
        print("Using cached scene", cached["id"])
        return cached["id"]
    response = requests.post(
        "https://planetarycomputer.microsoft.com/api/stac/v1/search",
        json={
            "collections": ["landsat-c2-l2"],
            "bbox": BBOX,
            "datetime": "2025-06-01T00:00:00Z/2025-08-31T23:59:59Z",
            "limit": 100,
        },
        timeout=60,
    )
    response.raise_for_status()
    catalog = response.json()
    if catalog.get("links") and any(x.get("rel") == "next" for x in catalog["links"]):
        raise RuntimeError("Catalog is paginated; narrow the search before selecting a scene")
    candidates = [x for x in catalog["features"] if "lwir11" in x["assets"]]
    scene = min(candidates, key=lambda x: (x["properties"].get("eo:cloud_cover", 100), x["id"]))
    print(scene["id"], flush=True)
    for band in ["red", "nir08", "lwir11", "qa_pixel", "qa_radsat"]:
        url = scene["assets"][band]["href"]
        signed = requests.get(
            "https://planetarycomputer.microsoft.com/api/sas/v1/sign", params={"href": url}, timeout=60
        )
        signed.raise_for_status()
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".TIF"):
            with rasterio.open(signed.json()["href"]) as src:
                bounds = transform_bounds("EPSG:4326", src.crs, *BBOX, densify_pts=21)
                window = from_bounds(*bounds, src.transform).round_offsets().round_lengths()
                values = src.read(1, window=window, boundless=True, fill_value=0)
                profile = src.profile.copy()
                profile.update(
                    height=values.shape[0],
                    width=values.shape[1],
                    transform=src.window_transform(window),
                    compress="deflate",
                )
                with rasterio.open(raw / f"{band}.tif", "w", **profile) as dst:
                    dst.write(values, 1)
        print(band, values.shape, flush=True)
    (raw / "scene.json").write_text(json.dumps(scene, ensure_ascii=False, indent=2), encoding="utf-8")
    provenance = ROOT / "data/provenance"
    provenance.mkdir(parents=True, exist_ok=True)
    (provenance / "scene.json").write_text(json.dumps(scene, ensure_ascii=False, indent=2), encoding="utf-8")
    return scene["id"]


if __name__ == "__main__":
    collect()
