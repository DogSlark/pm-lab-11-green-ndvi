"""Validate clean notebook state; optionally execute code cells against cached inputs."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(execute=False):
    for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
        notebook = json.loads(path.read_text(encoding="utf-8"))
        namespace = {"__name__": "__notebook__"}
        for index, cell in enumerate(notebook["cells"]):
            if cell["cell_type"] != "code":
                continue
            if cell.get("outputs") or cell.get("execution_count") is not None:
                raise ValueError(f"{path.name}: saved output/count in cell {index}")
            code = compile("".join(cell["source"]), f"{path.name}:cell{index}", "exec")
            if execute:
                exec(code, namespace)
        print("OK", path.name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    check(parser.parse_args().execute)
