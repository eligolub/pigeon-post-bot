# src/pigeon_mail_bot/services/sheets_store.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

import json
from pathlib import Path


@dataclass(frozen=True)
class SheetRow:
    ts_utc: str
    event: str
    user_id: int
    username: str | None
    name: str
    size: str
    from_city: str
    to_city: str
    date_human: str


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


class GoogleSheetsStore:
    def __init__(
        self,
        sheet_id: str,
        tab_name: str,
        *,
        sa_json_path: str | None = None,
        sa_json_content: str | None = None,
    ) -> None:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]

        if sa_json_content:
            info = json.loads(sa_json_content)
            creds = Credentials.from_service_account_info(info, scopes=scopes)
        elif sa_json_path:
            path = Path(sa_json_path)
            creds = Credentials.from_service_account_file(str(path), scopes=scopes)
        else:
            raise ValueError("Provide sa_json_content or sa_json_path")

        client = gspread.authorize(creds)
        sh = client.open_by_key(sheet_id)
        self.ws = sh.worksheet(tab_name)

    def append(self, row: SheetRow) -> None:
        self.ws.append_row(
            [
                row.ts_utc,
                row.event,
                str(row.user_id),
                row.username or "",
                row.name,
                row.size,
                row.from_city,
                row.to_city,
                row.date_human,
            ],
            value_input_option="USER_ENTERED",
        )
