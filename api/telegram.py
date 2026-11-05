"""Вебхук Telegram. Режим только чтения: пишем события в таблицу, ничего не отправляем."""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crm.events import parse_update  # noqa: E402
from crm.sheets import append_events  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")
        if not secret or self.headers.get("X-Telegram-Bot-Api-Secret-Token") != secret:
            self.send_response(403)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        try:
            update = json.loads(self.rfile.read(length) or b"{}")
            append_events(parse_update(update))
        except Exception as exc:  # Telegram повторяет апдейт при не-200, поэтому отвечаем 200
            print(f"update failed: {exc!r}")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"stepik_sale_boost webhook is alive")
