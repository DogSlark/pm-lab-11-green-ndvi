"""One source for WBS estimates, CPM, resource levelling, budget and risk simulation."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
# O/M/P are symmetric: expected hours equal M. Values are proposed estimates, not team votes.
TASKS = [
    ("A", "1.1", "Воспроизводимая загрузка", "Юрий", 8, []),
    ("B", "1.2", "Проверенные данные", "Айбулат", 8, ["A"]),
    ("G", "5.1", "CI и окружение", "Юрий", 8, ["A"]),
    ("C", "2.1", "Метрики NDVI и LST", "Айбулат", 10, ["B"]),
    ("D", "2.2", "Проверка кандидатов", "Марис", 12, ["B"]),
    ("E", "3.1", "Карта трёх слоёв", "Марис", 12, ["C"]),
    ("K", "5.2", "Регрессионные тесты", "Айбулат", 10, ["C", "G"]),
    ("F", "4.1", "Отчёт и ограничения", "Юрий", 8, ["C", "D"]),
    ("H", "3.2", "Публикация карты", "Марис", 6, ["E", "G"]),
    ("I", "4.2", "Приёмочные сценарии", "Айбулат", 6, ["F", "H", "K"]),
    ("L", "5.3", "Передача и воспроизводимость", "Марис", 8, ["I"]),
    ("J", "6.1", "Планы и контрольные точки", "Юрий", 12, []),
]
START = date(2026, 11, 23)
HOURS_PER_DAY = 1.2  # 6 hours/week/person; holidays must be agreed with sponsor.


def workdate(offset, finish=False):
    current = START
    remaining = max(0, int(np.ceil(offset)) - 1) if finish else int(np.floor(offset))
    while remaining:
        current += timedelta(days=1)
        if current.weekday() < 5:
            remaining -= 1
    return current.isoformat()


def schedule(hours, dependencies=None, dates=True):
    dependencies = dependencies or {t[0]: t[5] for t in TASKS}
    es, ef = {}, {}
    for index, task in enumerate(TASKS):
        key = task[0]
        es[key] = max((ef[p] for p in dependencies[key]), default=0)
        ef[key] = es[key] + float(hours[index]) / HOURS_PER_DAY
    finish = max(ef.values())
    lf, ls = {}, {}
    for task in reversed(TASKS):
        key = task[0]
        successors = [t[0] for t in TASKS if key in dependencies[t[0]]]
        lf[key] = min((ls[s] for s in successors), default=finish)
        ls[key] = lf[key] - (ef[key] - es[key])
    return [
        {
            "id": t[0],
            "wbs": t[1],
            "name": t[2],
            "owner": t[3],
            "hours": float(hours[i]),
            "predecessors": dependencies[t[0]],
            "ES": es[t[0]],
            "EF": ef[t[0]],
            "LS": ls[t[0]],
            "LF": lf[t[0]],
            "float": max(0, ls[t[0]] - es[t[0]]),
            "start": workdate(es[t[0]]) if dates else None,
            "finish": workdate(ef[t[0]], finish=True) if dates else None,
        }
        for i, t in enumerate(TASKS)
    ], finish


def levelled_dependencies():
    previous, result = {}, {}
    for task in TASKS:
        key, _, _, owner, _, predecessors = task
        result[key] = list(predecessors)
        if owner in previous and previous[owner] not in result[key]:
            result[key].append(previous[owner])
        previous[owner] = key
    return result


def calculate():
    hours = np.array([t[4] for t in TASKS], dtype=float)
    cpm, duration = schedule(hours)
    deps = levelled_dependencies()
    levelled, levelled_duration = schedule(hours, deps)
    # Beta-PERT: O=.5M, mode=M, P=1.5M, lambda=4 => beta(3,3).
    rng = np.random.default_rng(20261122)
    draws = hours * (0.5 + rng.beta(3, 3, size=(10000, len(hours))))
    # Fixed samples in all scenarios make comparisons meaningful.
    events = rng.random((10000, 4))
    risks = [
        {"id": "R1", "task": "B", "p_before": 0.45, "p_after": 0.15, "hours_before": 8, "hours_after": 4},
        {"id": "R2", "task": "D", "p_before": 0.35, "p_after": 0.15, "hours_before": 12, "hours_after": 6},
        {"id": "R3", "task": "E", "p_before": 0.25, "p_after": 0.10, "hours_before": 8, "hours_after": 4},
        {"id": "R8", "task": "C", "p_before": 0.30, "p_after": 0.10, "hours_before": 10, "hours_after": 3},
    ]
    target, buffer_end, reserve = levelled_duration, levelled_duration + 7, 16.2
    results, distribution = [], []
    critical_counts = np.zeros(len(hours))
    for scenario in ["estimates", "before", "after"]:
        sample = draws.copy()
        if scenario != "estimates":
            for rindex, risk in enumerate(risks):
                index = next(i for i, t in enumerate(TASKS) if t[0] == risk["task"])
                sample[:, index] += (events[:, rindex] < risk[f"p_{scenario}"]) * risk[f"hours_{scenario}"]
        finishes = np.zeros(10000)
        for n, row in enumerate(sample):
            tasks, finishes[n] = schedule(row, deps, dates=False)
            if scenario == "after":
                critical_counts += [t["float"] < 1e-7 for t in tasks]
        total = sample.sum(axis=1)
        results.append(
            {
                "scenario": scenario,
                "p_target": float((finishes <= target).mean()),
                "p_buffer": float((finishes <= buffer_end).mean()),
                "days_p50": float(np.percentile(finishes, 50)),
                "days_p85": float(np.percentile(finishes, 85)),
                "hours_p50": float(np.percentile(total, 50)),
                "hours_p85": float(np.percentile(total, 85)),
                "p_budget": float((total <= hours.sum() + reserve).mean()),
            }
        )
        distribution.append(finishes)
    investment, support, benefit, rate = 108000, 18000, 90000, 0.2
    factor = sum(1 / (1 + rate) ** t for t in range(1, 4))
    budget = {
        "base": investment,
        "risk_reserve": 16200,
        "management_reserve": 5400,
        "total": 129600,
        "support_year": support,
        "benefit_year": benefit,
        "tco_3y": investment + 3 * support,
        "npv": -investment + (benefit - support) * factor,
        "roi": (3 * benefit - investment - 3 * support) / (investment + 3 * support),
        "payback_years": investment / (benefit - support),
        "break_even_benefit": support + investment / factor,
        "sensitivity": {str(b): -investment + (b - support) * factor for b in [60000, 75000, 90000]},
    }
    output = {
        "start": START.isoformat(),
        "capacity_hours_per_day": HOURS_PER_DAY,
        "hours": float(hours.sum()),
        "sigma_hours": float(np.sqrt(np.sum((hours / 6) ** 2))),
        "cpm_days": duration,
        "levelled_days": levelled_duration,
        "buffer_end_days": buffer_end,
        "finish": workdate(levelled_duration, finish=True),
        "buffer_end": workdate(buffer_end, finish=True),
        "cpm": cpm,
        "levelled": levelled,
        "risks": risks,
        "monte_carlo": results,
        "budget": budget,
        "criticality": {t[0]: float(critical_counts[i] / 10000) for i, t in enumerate(TASKS)},
        "sensitivity": {
            t[0]: float(np.corrcoef(draws[:, i], distribution[-1])[0, 1]) for i, t in enumerate(TASKS)
        },
    }
    path = ROOT / "data/processed/plan.json"
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    fig, ax = plt.subplots(figsize=(9, 5))
    for values, label in zip(
        distribution, ["Estimates only", "Before mitigation", "After mitigation"], strict=True
    ):
        ax.hist(values, bins=60, histtype="step", density=True, label=label)
    ax.axvline(target, color="#333333", linestyle="--", label="Baseline target")
    ax.axvline(buffer_end, color="#2b8c7f", linestyle="--", label="Buffer end")
    ax.set(
        xlabel="Working days from start", ylabel="Density", title="Green-NDVI | 10,000 beta-PERT simulations"
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(ROOT / "docs/img/monte_carlo.png", dpi=160)
    plt.close(fig)
    print(
        json.dumps(
            {k: v for k, v in output.items() if k not in ["cpm", "levelled"]}, ensure_ascii=False, indent=2
        )
    )
    return output


if __name__ == "__main__":
    calculate()
