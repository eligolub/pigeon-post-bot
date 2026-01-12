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
    route: str
    date: str
    created_at_utc: str


class JsonlFileStore:
    """
    MVP storage: JSON Lines file (one JSON object per line).
    Good enough for append-only logs; easy to migrate later.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append_want_to_send(self, record: WantToSendRecord) -> None:
        line = json.dumps(asdict(record), ensure_ascii=False)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
