"""Пересчёт баллов: events -> scores. Запускается кроном Vercel раз в день."""

import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crm.scoring import rescore  # noqa: E402
from crm.sheets import read_events, write_scores  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        cron_secret = os.environ.get("CRON_SECRET", "")
        if not cron_secret or self.headers.get("Authorization") != f"Bearer {cron_secret}":
            self.send_response(403)
            self.end_headers()
            return
        cards = rescore(read_events())
        write_scores(cards)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(f"rescored {len(cards)} people".encode())
