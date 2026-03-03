import os

import requests

LINE_API_URL = "https://api.line.me/v2/bot/message/push"
MAX_LINE_CHARS = 4900


def send_line_message(text: str) -> None:
    token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
    user_id = os.environ["LINE_USER_ID"]

    if len(text) > MAX_LINE_CHARS:
        text = text[:MAX_LINE_CHARS] + "..."

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    payload = {
        "to": user_id,
        "messages": [{"type": "text", "text": text}],
    }
    resp = requests.post(LINE_API_URL, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    print(f"[LINE] sent: {resp.status_code}")


def build_message(changes: list[dict]) -> str:
    """
    changes: [{ "url": str, "summary": str }, ...]
    """
    lines = ["[宮越ホールディングス] サイト更新を検知しました\n"]
    for i, ch in enumerate(changes, 1):
        lines.append(f"{i}. {ch['url']}")
        lines.append(f"変更箇所（抜粋）:")
        lines.append(ch["summary"])
        lines.append("")
    return "\n".join(lines).strip()
