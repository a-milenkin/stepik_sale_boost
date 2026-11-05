"""Регистрирует вебхук бота. Запуск локально:

    TELEGRAM_BOT_TOKEN=... TELEGRAM_WEBHOOK_SECRET=... \
    python scripts/set_webhook.py https://<проект>.vercel.app/api/telegram
"""

import json
import os
import sys
import urllib.parse
import urllib.request

ALLOWED = [
    "message",               # комментарии в группах обсуждений
    "chat_member",           # вступления и выходы из каналов
    "chat_join_request",     # заявки по ссылкам с YouTube
    "business_connection",   # подключение к профилю
    "business_message",      # личка @Aleron_df
]

url = sys.argv[1]
token = os.environ["TELEGRAM_BOT_TOKEN"]
data = urllib.parse.urlencode({
    "url": url,
    "secret_token": os.environ["TELEGRAM_WEBHOOK_SECRET"],
    "allowed_updates": json.dumps(ALLOWED),
    "drop_pending_updates": "true",
}).encode()
with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/setWebhook", data) as r:
    print(r.read().decode())
