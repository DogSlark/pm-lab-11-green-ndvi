# Реестр источников
Срез загрузки: 22.11.2026. Оценки 1–5: больше — лучше. Это экспертная предварительная оценка, не измеренная полнота.

| ID | Источник и точная ссылка | Данные / период | Лицензия | Полнота / точность / актуальность / доступность | Решение |
|---|---|---|---|---|---|
| S1 | [USGS Landsat C2 L2](https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products), [STAC item](https://planetarycomputer.microsoft.com/api/stac/v1/collections/landsat-c2-l2/items/LC09_L2SP_171021_20250708_02_T1) | Landsat 9, 08.07.2025, SR_B4/B5, ST_B10, QA | USGS public domain; источник обязателен по правилам проекта | 4 / 4 / 3 / 4 | Основной NDVI и LST; 30 м сетка, тепловой канал исходно 100 м |
| S2 | [OSM relation 3437391](https://www.openstreetmap.org/relation/3437391), [районы 2133461–2133467](https://www.openstreetmap.org/relation/2133461) | Город и 7 районов; текущий срез OSM | [ODbL](https://www.openstreetmap.org/copyright) | 4 / 3 / 4 / 3 | Границы для агрегации; версии не совпадают по дате со снимком |
| S3 | [Copernicus Sentinel-2](https://dataspace.copernicus.eu/explore-data/data-collections/sentinel-data/sentinel-2) | Спектральные снимки, 10 м | Условия Copernicus Sentinel | 4 / 4 / 4 / 3 | Резерв/расширение; НЕ загружен и НЕ использован в текущих цифрах |
| S4 | [Официальный портал Казани](https://kzn.ru/) | Административная структура и контекст | Лицензия на машинные геоданные не подтверждена | 3 / 4 / 4 / 2 | Для проверки названий; не копировать базу без разрешения |

## Поля и происхождение
boundary/districts: osm_id, name, geometry; EPSG:4326, производные OSM ODbL.
district_statistics.csv: total_pixels, valid_pixels, valid_fraction, mean_ndvi, mean_lst_c, priority_km2; производный расчёт.
priority_zones: zone_id, area_ha, geometry; крупные связные кластеры >=0.5 га, не согласованные участки посадок.
NDVI/LST: физические величины float32, NoData=-9999, CRS исходного снимка (см. raster metadata).
Сырые снимки не коммитятся; unsigned STAC item и ответы Nominatim в data/provenance. Подписанные SAS URL в репозиторий не сохраняются.

## Ограничения
Снимок показывает один момент лета 2025, а не климат и не температуру воздуха. Тепловая сетка 30 м не создаёт детализацию 30 м. Связь NDVI–LST не доказывает эффект новых посадок. Данные о населении и динамике 3–5 лет не загружены — таких выводов нет.
