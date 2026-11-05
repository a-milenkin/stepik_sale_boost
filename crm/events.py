"""Разбор Telegram-апдейтов в события для листа events.

Режим "только читаю": функция ничего не отправляет, она только
превращает апдейт в список строк для записи.
"""

import os
import re
from datetime import datetime, timezone

COURSE_QUESTION = re.compile(
    r"\b(курс\w*|цен\w*|стоимост\w*|сколько стоит|программ\w*|поток\w*|оплат\w*)\b",
    re.IGNORECASE,
)


def _env_int(name: str) -> int | None:
    v = os.environ.get(name, "").strip()
    return int(v) if v.lstrip("-").isdigit() else None


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _who(user: dict) -> dict:
    name = " ".join(x for x in (user.get("first_name"), user.get("last_name")) if x)
    return {"user_id": str(user.get("id", "")), "username": user.get("username", ""), "name": name}


def _row(event: str, user: dict, source: str = "", detail: str = "") -> dict:
    return {"ts": _now(), "event": event, **_who(user), "source": source, "detail": detail[:200]}


def parse_update(update: dict) -> list[dict]:
    """Апдейт -> строки для листа events. Событие replied считает rescore()."""
    owner = _env_int("OWNER_USER_ID")
    saas_id = _env_int("CHANNEL_SAAS_ID")
    rows: list[dict] = []

    # 1. Заявка на вступление в канал (ссылки из YouTube)
    if req := update.get("chat_join_request"):
        link = (req.get("invite_link") or {}).get("name", "")
        user = req["from"]
        if link.lower().startswith("yt"):
            rows.append(_row("youtube_join_request", user, source=link))
        else:
            rows.append(_row("join_request", user, source=link))

    # 2. Вступление и выход из каналов
    if cm := update.get("chat_member"):
        chat_id = cm["chat"]["id"]
        old, new = cm["old_chat_member"]["status"], cm["new_chat_member"]["status"]
        user = cm["new_chat_member"]["user"]
        joined = old in ("left", "kicked") and new in ("member", "administrator")
        left = old in ("member", "restricted") and new in ("left", "kicked")
        if joined:
            rows.append(_row("joined_saas" if chat_id == saas_id else "joined_channel", user,
                             source=str(chat_id), detail=(cm.get("invite_link") or {}).get("name", "")))
        elif left:
            rows.append(_row("left_channel", user, source=str(chat_id)))

    # 3. Комментарии в группах обсуждений
    msg = update.get("message")
    if msg and msg["chat"]["type"] in ("group", "supergroup") and msg.get("from"):
        if not msg["from"].get("is_bot"):
            rows.append(_row("comment", msg["from"], source=str(msg["chat"]["id"]),
                             detail=msg.get("text") or msg.get("caption") or ""))

    # 4. Личка @Aleron_df через Secretary/Business-подключение
    if bm := update.get("business_message"):
        sender = bm.get("from") or {}
        chat_user = bm["chat"]  # в личке chat = собеседник
        peer = {"id": chat_user["id"], "username": chat_user.get("username", ""),
                "first_name": chat_user.get("first_name", ""), "last_name": chat_user.get("last_name", "")}
        text = bm.get("text") or bm.get("caption") or ""
        if owner and sender.get("id") == owner:
            # исходящее от Алерона: фиксируем, что человек получил
            if bm.get("voice") or bm.get("video_note"):
                rows.append(_row("got_voice", peer, source="dm"))
            if bm.get("document") or "http" in text:
                rows.append(_row("got_guide", peer, source="dm", detail=text))
            rows.append(_row("outgoing", peer, source="dm", detail=text))
        else:
            rows.append(_row("dm_incoming", peer, source="dm", detail=text))
            if COURSE_QUESTION.search(text):
                rows.append(_row("asked_course", peer, source="dm", detail=text))

    if bc := update.get("business_connection"):
        rows.append(_row("business_connection", bc["user"], detail=f"enabled={bc.get('is_enabled')}"))

    return rows
