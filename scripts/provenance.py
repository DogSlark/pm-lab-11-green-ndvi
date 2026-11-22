"""Record reproducibility hashes without copying raw rasters into Git."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
paths = sorted((ROOT / "data/raw").glob("*.tif"))
paths += sorted((ROOT / "data/processed").glob("*"))
records = []
for path in paths:
    if path.is_file() and path.suffix != ".gitkeep":
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        records.append(
            {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": digest}
        )
(ROOT / "data/provenance/checksums.json").write_text(
    json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
)
print(f"Recorded {len(records)} input/output hashes")
