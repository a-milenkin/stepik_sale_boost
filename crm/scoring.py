"""Скоринг по лестнице Ханта.

Бот пишет в лист events сырые события, rescore() сворачивает их в баллы
по каждому человеку. Веса и лимиты правим здесь.
"""

from collections import defaultdict

# событие -> (баллы за одно событие, максимум баллов за этот тип)
WEIGHTS = {
    "youtube_join_request": (1, 1),   # пришёл по ссылке-заявке с YouTube
    "joined_saas": (1, 1),            # подписался на aleron_saas
    "comment": (1, 3),                # комментарий в группе обсуждений
    "dm_incoming": (2, 2),            # сам написал в личку
    "replied": (2, 2),                # ответил после нашего сообщения
    "got_guide": (1, 3),              # получил гайд (документ или ссылку)
    "got_voice": (1, 1),              # получил голосовое или кружок
    "asked_course": (3, 3),           # спросил про курс, цену, программу
    "left_channel": (-1, -1),         # отписался
}

# (нижняя граница балла, название ступени)
STAGES = [
    (10, "5. Готов купить"),
    (7, "4. Знает о курсе"),
    (4, "3. Знает о решениях"),
    (2, "2. Знает о проблеме"),
    (0, "1. Не знает о проблеме"),
]


def stage_for(score: int) -> str:
    for low, name in STAGES:
        if score >= low:
            return name
    return STAGES[-1][1]


def rescore(events: list[dict]) -> dict[str, dict]:
    """events: строки листа events. Возвращает {user_id: карточка}."""
    totals: dict[str, dict] = defaultdict(lambda: defaultdict(int))
    meta: dict[str, dict] = {}

    waiting_reply: set[str] = set()  # кому мы написали и ещё не получили ответ
    for e in events:
        uid = str(e.get("user_id") or "")
        etype = e.get("event")
        if etype == "outgoing":
            waiting_reply.add(uid)
            continue
        if etype == "dm_incoming" and uid in waiting_reply:
            etype = "replied"
            waiting_reply.discard(uid)
        if not uid or etype not in WEIGHTS:
            continue
        points, cap = WEIGHTS[etype]
        cur = totals[uid][etype]
        if cap >= 0:
            totals[uid][etype] = min(cur + points, cap)
        else:
            totals[uid][etype] = max(cur + points, cap)
        m = meta.setdefault(uid, {"username": "", "name": "", "first_seen": e.get("ts", "")})
        m["username"] = e.get("username") or m["username"]
        m["name"] = e.get("name") or m["name"]
        m["last_seen"] = e.get("ts", "")

    cards = {}
    for uid, by_type in totals.items():
        score = sum(by_type.values())
        cards[uid] = {
            **meta[uid],
            "user_id": uid,
            "score": score,
            "stage": stage_for(score),
            "breakdown": ", ".join(f"{k}:{v}" for k, v in sorted(by_type.items()) if v),
        }
    return cards
