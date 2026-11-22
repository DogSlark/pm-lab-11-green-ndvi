# Green-NDVI: озеленение и тепловые острова Казани
Вариант11 · Казань. Анализ реального Landsat9 от08.07.2025: NDVI, температура поверхности и зоны для дальнейшего обследования.

![ci](https://github.com/DogSlark/pm-lab-11-green-ndvi/actions/workflows/ci.yml/badge.svg)

## Команда
| Участник | GitHub | ЛР1 | ЛР2 (предложение) | ЛР3 (предложение) | ЛР4 (предложение) |
|---|---|---|---|---|---|
| Юрий | @DogSlark | Менеджер | Данные/платформа | Аналитик | Менеджер |
| Айбулат | @xacker69 | Аналитик | Менеджер/владелец продукта | Данные | Аналитика/качество |
| Марис | @SpoNNN | Технический организатор | Геоаналитик | Менеджер | Интерфейс/риски |
Ротация требует подтверждения команды. Другие участники в команду не добавлены.

## Результаты
- [Качество и измеренные результаты](docs/data-quality.md), [CSV районов](data/processed/district_statistics.csv).
- [NDVI](docs/img/ndvi.png), [температура](docs/img/temperature.png), [интерактивная HTML-карта](docs/maps/kazan.html) (скачать и открыть).
- [Инструкция воспроизведения](data/README.md), [источники](data/sources.md).
- [Доска](https://github.com/users/DogSlark/projects/1/views/1).

## Лабораторные
| ЛР | Материалы | Состояние |
|---|---|---|
|1|[Устав](docs/charter.md), [договор](docs/team-agreement.md), [бизнес-кейс](docs/business-case.md), [RACI](docs/stakeholders.md)|Есть релиз v0.1-initiation; ранее выявленные замечания остаются|
|2|[Требования](docs/requirements.md), [WBS](docs/wbs.md), [DoR/DoD](docs/definition-of-done.md), [данные](docs/data-quality.md)|Подготовлено для review; решения заказчика ожидаются|
|3|[Оценки](docs/estimation.md), [план](docs/schedule.md), [бюджет](docs/budget.md), [коммуникации](docs/communication-plan.md), [Sprint1](docs/sprint-1.md)|Проект baseline; календарь и оценки командой не утверждены|
|4|[Риски](docs/risk-register.md), [качество](docs/quality-plan.md), [правила](CONTRIBUTING.md), [статус](docs/status-report-1.md)|Код и локальная проверка подготовлены; обзор/ревью и завершение спринта ожидаются|
В начале ЛР запускать Actions→Bootstrap с номером2/3/4. Формальные релизы v0.2-scope/v0.3-plan/v0.4 выпускать после выполнения критериев и человеческого ревью. Подготовленные документы не означают, что встречи проведены или проект принят.

## Ограничения
LST — температура поверхности в момент пролёта, не воздуха. NDVI–LST не доказывает эффект новых посадок. Десять кластеров ещё не проверены на пригодность для озеленения. Тепловой канал100м пересэмплирован на30м. Календарные даты плана сценарные, праздники требуют уточнения.
© [участники OpenStreetMap](https://www.openstreetmap.org/copyright), ODbL; USGS Landsat9 Collection2 L2. Производные OSM-слои — ODbL.
