# Воспроизведение данных Green-NDVI

Python 3.12+; из корня проекта:
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate; Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/collect_landsat.py
python scripts/collect_nominatim.py
python scripts/analyze.py
python scripts/plan.py
python scripts/validate_data.py
pytest -q
```
Нужен интернет только для получения снимков, границ и картографической подложки. Загружаются пространственные окна пяти TIFF, а не целая сцена. Сеть и открытые сервисы могут отказать; ошибки не маскируются под успешный анализ.

Landsat: поиск bbox [48.85,55.55,49.45,56.0], лето 2025, выбирается минимальная облачность среди результатов. Точный выбранный item сохранён в provenance/scene.json. Для неизменного повторения используйте этот item; если каталог обновился, смену сцены оформляйте отдельно.
Nominatim: один запрос в секунду, результаты кэшируются; семь районов перечислены в scripts/collect_nominatim.py. Ответы — provenance/boundary-*.json. Overpass пробовался и вернул ошибку; резервный Nominatim сработал.

raw/ — исходные TIFF, не хранится в Git; processed/ — небольшие итоговые растры, GPKG, GeoJSON, CSV и JSON; provenance/ — метаданные и контрольные суммы. manual/ не используется: таблица населения из учебного AquaMap удалена, население не анализируется.

Проверка provenance: scripts/provenance.py создаёт SHA-256 для входов и результатов. Чтобы повторить именно опубликованный расчёт, сверяйте хеши, а не только имя сцены.

© участники OpenStreetMap, https://www.openstreetmap.org/copyright (ODbL). Снимок: USGS Landsat 9 Collection 2 L2. Производные границы и таблицы со связью с OSM распространяются по ODbL; код — по лицензии репозитория, отдельная лицензия кода пока не установлена.
