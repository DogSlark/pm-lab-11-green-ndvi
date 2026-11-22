import importlib.util
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location("plan", Path(__file__).parents[1] / "scripts/plan.py")
plan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan)


def test_schedule_waits_for_all_predecessors():
    rows, _ = plan.schedule([t[4] for t in plan.TASKS], dates=False)
    by_id = {r["id"]: r for r in rows}
    assert by_id["I"]["ES"] == max(by_id[k]["EF"] for k in ["F", "H", "K"])
    assert all(r["float"] >= 0 for r in rows)


def test_levelled_work_does_not_overlap_for_one_person():
    rows, _ = plan.schedule([t[4] for t in plan.TASKS], plan.levelled_dependencies(), dates=False)
    availability = {}
    for row in rows:
        assert row["ES"] >= availability.get(row["owner"], 0) - 1e-10
        availability[row["owner"]] = row["EF"]


def test_pert_mean_and_sigma():
    hours = np.array([t[4] for t in plan.TASKS])
    assert hours.sum() == 108
    assert np.sqrt(np.sum((hours / 6) ** 2)) == pytest.approx(5.333333333)
