"""Idempotent repository tracker setup using the Actions token through gh CLI."""

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = os.environ["GITHUB_REPOSITORY"]


def api(method, path, payload=None):
    command = ["gh", "api", "--method", method, path]
    if payload is not None:
        command += ["--input", "-"]
    result = subprocess.run(
        command,
        input=json.dumps(payload) if payload is not None else None,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout) if result.stdout.strip() else None


def sync():
    config = json.loads((ROOT / "data/tracker.json").read_text(encoding="utf-8"))
    milestones = api("GET", f"repos/{REPO}/milestones?state=all&per_page=100")
    ms = {m["title"]: m["number"] for m in milestones}
    for title in ["ЛР2: Требования и данные", "ЛР3: Планирование", "ЛР4: Риски и качество"]:
        if title not in ms:
            ms[title] = api("POST", f"repos/{REPO}/milestones", {"title": title})["number"]
    for name in ["Must", "Should", "Could", "Won't"]:
        subprocess.run(
            ["gh", "label", "create", name, "--color", "BFD4F2", "--force", "--repo", REPO],
            check=True,
            capture_output=True,
        )
    result = subprocess.run(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            REPO,
            "--state",
            "all",
            "--limit",
            "500",
            "--json",
            "number,title,id",
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    existing = {i["title"]: i for i in json.loads(result.stdout)}
    created = {}
    for entry in config:
        title = entry["title"]
        if title in existing:
            issue = api("GET", f"repos/{REPO}/issues/{existing[title]['number']}")
        else:
            issue = api(
                "POST",
                f"repos/{REPO}/issues",
                {
                    "title": title,
                    "body": entry["body"],
                    "labels": entry["labels"],
                    "assignees": entry.get("assignees", ["DogSlark"]),
                    "milestone": ms[entry.get("milestone", "ЛР2: Требования и данные")],
                },
            )
        created[entry["key"]] = issue
        if entry.get("parent"):
            parent = created[entry["parent"]]
            children = api("GET", f"repos/{REPO}/issues/{parent['number']}/sub_issues")
            if not any(c["id"] == issue["id"] for c in children):
                api(
                    "POST",
                    f"repos/{REPO}/issues/{parent['number']}/sub_issues",
                    {"sub_issue_id": issue["id"]},
                )
        print(entry["key"], issue["html_url"])
    print("Tracker ready. Project fields and human approvals remain separate.")


if __name__ == "__main__":
    sync()
