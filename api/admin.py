"""Служебные действия с ботом без выноса токена наружу.

GET /api/admin?key=<ADMIN_SECRET>&action=<действие>
  me            - getMe, проверка токена
  webhook_info  - getWebhookInfo
  set_webhook   - регистрирует вебхук на /api/telegram этого же домена
  chat&chat=@x  - getChat, чтобы узнать числовой id канала
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ALLOWED_UPDATES = ["message", "chat_member", "chat_join_request", "business_connection", "business_message"]


def tg(method: str, params: dict | None = None) -> dict:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    data = urllib.parse.urlencode(params or {}).encode()
    with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/{method}", data, timeout=15) as r:
        return json.loads(r.read())


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        key = os.environ.get("ADMIN_SECRET", "")
        if not key or q.get("key", [""])[0] != key:
            self.send_response(403)
            self.end_headers()
            return

        action = q.get("action", ["me"])[0]
        try:
            if action == "me":
                res = tg("getMe")
            elif action == "webhook_info":
                res = tg("getWebhookInfo")
            elif action == "set_webhook":
                host = os.environ.get("VERCEL_PROJECT_PRODUCTION_URL") or self.headers.get("Host")
                res = tg("setWebhook", {
                    "url": f"https://{host}/api/telegram",
                    "secret_token": os.environ["TELEGRAM_WEBHOOK_SECRET"],
                    "allowed_updates": json.dumps(ALLOWED_UPDATES),
                    "drop_pending_updates": "true",
                })
            elif action == "chat":
                res = tg("getChat", {"chat_id": q.get("chat", [""])[0]})
                r = res.get("result", {})
                res = {"ok": res.get("ok"), "id": r.get("id"), "title": r.get("title"),
                       "type": r.get("type"), "linked_chat_id": r.get("linked_chat_id")}
            else:
                res = {"ok": False, "error": "unknown action"}
        except Exception as exc:
            res = {"ok": False, "error": repr(exc)}

        body = json.dumps(res, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)
