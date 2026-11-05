"""Хранилище в Google Sheets: лист events (сырые события) и лист scores (баллы).

Доступ через сервисный аккаунт: JSON ключа лежит в переменной
GOOGLE_SERVICE_ACCOUNT_JSON, id таблицы в CRM_SPREADSHEET_ID.
Таблицу нужно расшарить на email сервисного аккаунта (редактор).
"""

import json
import os

import gspread

EVENT_COLS = ["ts", "event", "user_id", "username", "name", "source", "detail"]
SCORE_COLS = ["user_id", "username", "name", "score", "stage", "breakdown", "first_seen", "last_seen"]


def _book():
    creds = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    gc = gspread.service_account_from_dict(creds)
    return gc.open_by_key(os.environ["CRM_SPREADSHEET_ID"])


def _sheet(book, title: str, cols: list[str]):
    try:
        ws = book.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = book.add_worksheet(title=title, rows=1000, cols=len(cols))
        ws.append_row(cols)
    return ws


def append_events(rows: list[dict]) -> None:
    if not rows:
        return
    ws = _sheet(_book(), "events", EVENT_COLS)
    ws.append_rows([[r.get(c, "") for c in EVENT_COLS] for r in rows], value_input_option="RAW")


def read_events() -> list[dict]:
    ws = _sheet(_book(), "events", EVENT_COLS)
    return ws.get_all_records()


def write_scores(cards: dict[str, dict]) -> None:
    ws = _sheet(_book(), "scores", SCORE_COLS)
    ordered = sorted(cards.values(), key=lambda c: c["score"], reverse=True)
    ws.clear()
    ws.update([SCORE_COLS] + [[c.get(k, "") for k in SCORE_COLS] for c in ordered], "A1")
