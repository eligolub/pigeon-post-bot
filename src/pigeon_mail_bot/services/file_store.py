from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class WantToSendRecord:
    user_id: int
    username: str | None
    name: str
    from_city: str
    to_city: str
    date: str
    size: str
    created_at_utc: str


@dataclass(frozen=True)
class CanDeliverRecord:
    user_id: int
    username: str | None
    name: str
    from_city: str
    to_city: str
    date: str
    size: str
    created_at_utc: str


class JsonlFileStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: object) -> None:
        line = json.dumps(asdict(record), ensure_ascii=False)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
