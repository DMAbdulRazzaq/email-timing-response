import json
from pathlib import Path
from typing import Any


class JsonlStore:
    """Append-only JSONL event store for feedback, recommendations, and analytics."""

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: dict[str, Any]) -> None:
        with open(self.path, "a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []

        records = []
        with open(self.path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
