"""Generate reproducible district statistics and maps from real Landsat/OSM."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import folium
import geopandas as gpd
import matplotlib
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.features import geometry_mask, shapes
from rasterio.warp import calculate_default_transform, reproject, transform_bounds
from shapely.geometry import shape

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from ndvi import clear_land, ndvi, priority_mask, temperature_c  # noqa: E402


def analyze():
    processed = ROOT / "data/processed"
    boundary = gpd.read_file(processed / "boundary.gpkg")
    districts = gpd.read_file(processed / "districts.gpkg")
    districts.geometry = districts.geometry.intersection(boundary.geometry.iloc[0])
    bands = {}
    for name in ["red", "nir08", "lwir11", "qa_pixel", "qa_radsat"]:
        with rasterio.open(ROOT / f"data/raw/{name}.tif") as src:
            bands[name] = src.read(1)
            if name == "red":
                profile = src.profile.copy()
                transform, crs = src.transform, src.crs
            elif src.transform != transform or src.crs != crs or src.shape != bands["red"].shape:
                raise ValueError("Input bands do not share one grid")
    inside = geometry_mask(boundary.to_crs(crs).geometry, bands["red"].shape, transform, invert=True)
    vegetation = ndvi(bands["red"], bands["nir08"])
    temperature = temperature_c(bands["lwir11"])
    clear = clear_land(bands["qa_pixel"], bands["qa_radsat"]) & inside
    valid = clear & np.isfinite(vegetation) & np.isfinite(temperature)
    vegetation[~valid] = np.nan
    temperature[~valid] = np.nan
    threshold = float(np.nanpercentile(temperature, 75))
    priority = priority_mask(vegetation, temperature, threshold)
    profile.update(dtype="float32", nodata=-9999, count=1, compress="deflate")
    for name, values in [("ndvi", vegetation), ("temperature", temperature)]:
        with rasterio.open(processed / f"{name}.tif", "w", **profile) as dst:
            dst.write(np.where(np.isfinite(values), values, -9999).astype("float32"), 1)
    rows = []
    for _, district in districts.to_crs(crs).iterrows():
        mask = geometry_mask([district.geometry], inside.shape, transform, invert=True) & inside
        n = int((mask & valid).sum())
        rows.append(
            {
                "osm_id": district.osm_id,
                "name": district["name"],
                "total_pixels": int(mask.sum()),
                "valid_pixels": n,
                "valid_fraction": n / int(mask.sum()) if mask.any() else 0,
                "mean_ndvi": float(np.nanmean(vegetation[mask])) if n else None,
                "mean_lst_c": float(np.nanmean(temperature[mask])) if n else None,
                "priority_km2": float((mask & priority).sum() * 900 / 1e6),
            }
        )
    import pandas as pd

    table = pd.DataFrame(rows)
    table.to_csv(processed / "district_statistics.csv", index=False)
    district_metrics = districts.merge(table, on=["osm_id", "name"])
    district_metrics.to_file(processed / "district_metrics.gpkg", driver="GPKG")
    polygons = [
        shape(geom)
        for geom, value in shapes(priority.astype("uint8"), mask=priority, transform=transform)
        if value == 1
    ]
    # Candidate clusters >= 0.5 ha; remote sensing cannot establish plantability.
    zones = gpd.GeoDataFrame({"geometry": polygons}, crs=crs)
    zones["area_ha"] = zones.area / 10000
    zones = zones[zones.area_ha >= 0.5].sort_values("area_ha", ascending=False).head(10).copy()
    zones["zone_id"] = range(1, len(zones) + 1)
    zones.to_crs(4326).to_file(processed / "priority_zones.gpkg", driver="GPKG")
    zones.to_crs(4326).to_file(processed / "priority_zones.geojson", driver="GeoJSON")
    img = ROOT / "docs/img"
    img.mkdir(exist_ok=True)
    for name, values, cmap, limits, label in [
        ("ndvi", vegetation, "YlGn", (0, 1), "NDVI"),
        ("temperature", temperature, "inferno", (20, 50), "Surface temperature, C"),
    ]:
        fig, ax = plt.subplots(figsize=(9, 8))
        extent = rasterio.transform.array_bounds(*inside.shape, transform)
        im = ax.imshow(
            values,
            cmap=cmap,
            vmin=limits[0],
            vmax=limits[1],
            extent=[extent[0], extent[2], extent[1], extent[3]],
        )
        districts.to_crs(crs).boundary.plot(ax=ax, color="#243746", linewidth=0.6)
        fig.colorbar(im, ax=ax, label=label, shrink=0.7)
        ax.set_title("Kazan | Landsat 9 | 2025-07-08")
        ax.set_axis_off()
        fig.text(0.1, 0.03, "USGS Landsat; OSM contributors (ODbL) | White: water/cloud/no data", fontsize=9)
        fig.savefig(img / f"{name}.png", dpi=160, bbox_inches="tight")
        plt.close(fig)
    map_ = folium.Map(location=[55.79, 49.12], zoom_start=10, tiles="OpenStreetMap")
    # Warp the visual image to Web Mercator before placing it over OSM.
    source_bounds = rasterio.transform.array_bounds(*inside.shape, transform)
    dst_transform, width, height = calculate_default_transform(
        crs, "EPSG:3857", inside.shape[1], inside.shape[0], *source_bounds, dst_width=700, dst_height=700
    )
    west, south, east, north = transform_bounds(crs, "EPSG:4326", *source_bounds, densify_pts=21)
    for title, values, cmap, low, high in [
        ("NDVI · 08.07.2025", vegetation, "YlGn", 0, 1),
        ("LST °C · 08.07.2025", temperature, "inferno", 20, 50),
    ]:
        dest = np.full((height, width), np.nan, dtype="float32")
        reproject(
            values.astype("float32"),
            dest,
            src_transform=transform,
            src_crs=crs,
            dst_transform=dst_transform,
            dst_crs="EPSG:3857",
            src_nodata=np.nan,
            dst_nodata=np.nan,
            resampling=Resampling.bilinear,
        )
        rgba = plt.get_cmap(cmap)(np.clip((dest - low) / (high - low), 0, 1))
        rgba[:, :, 3] = np.isfinite(dest) * 0.8
        folium.raster_layers.ImageOverlay(
            rgba, bounds=[[south, west], [north, east]], name=title, opacity=0.85, show=False
        ).add_to(map_)
    folium.GeoJson(
        district_metrics.to_json(),
        name="Районы: NDVI и температура",
        tooltip=folium.GeoJsonTooltip(
            fields=["name", "mean_ndvi", "mean_lst_c", "valid_fraction", "priority_km2"]
        ),
    ).add_to(map_)
    folium.GeoJson(
        zones.to_crs(4326).to_json(),
        name="Кандидаты для проверки",
        style_function=lambda _: {"color": "#de4a32", "fillOpacity": 0.65},
        tooltip=folium.GeoJsonTooltip(fields=["zone_id", "area_ha"]),
    ).add_to(map_)
    folium.LayerControl().add_to(map_)
    banner = """<div style="position:fixed;top:10px;left:60px;z-index:9999;background:white;
    padding:12px;max-width:440px">Казань · Landsat 9 · 08.07.2025<br>
    Кандидаты: NDVI &lt; 0.3, LST ≥ P75. Не план посадок и не температура воздуха.
    <br>NDVI: жёлтый 0 → зелёный 1; LST: тёмный 20 → жёлтый 50°C.
    <br>© участники OpenStreetMap · USGS Landsat</div>"""
    map_.get_root().html.add_child(folium.Element(banner))
    (ROOT / "docs/maps").mkdir(exist_ok=True)
    map_.save(str(ROOT / "docs/maps/kazan.html"))
    summary = {
        "scene_id": "LC09_L2SP_171021_20250708_02_T1",
        "threshold_lst_c": threshold,
        "city_pixels": int(inside.sum()),
        "valid_land_pixels": int(valid.sum()),
        "valid_fraction_of_city": float(valid.sum() / inside.sum()),
        "priority_land_km2": float(priority.sum() * 0.0009),
        "zones": len(zones),
        "correlation_ndvi_lst": float(np.corrcoef(vegetation[valid], temperature[valid])[0, 1]),
        "districts": rows,
    }
    (processed / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    analyze()
