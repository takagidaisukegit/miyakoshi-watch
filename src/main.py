import json
import sys
from pathlib import Path

from scraper import crawl
from differ import extract_summary
from notifier import send_line_message, build_message

SNAPSHOT_PATH = Path(__file__).parent.parent / "data" / "snapshots.json"


def load_snapshots() -> dict:
    if SNAPSHOT_PATH.exists():
        return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    return {}


def save_snapshots(data: dict) -> None:
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main():
    print("[START] crawling...")
    current = crawl()

    old_snapshots = load_snapshots()
    is_baseline = len(old_snapshots) == 0

    changes = []
    for url, data in current.items():
        if url not in old_snapshots:
            # 新規発見ページは変更扱いにしない
            continue
        if old_snapshots[url]["hash"] != data["hash"]:
            print(f"[CHANGED] {url}")
            changes.append({
                "url": url,
                "old_text": old_snapshots[url]["text"],
                "new_text": data["text"],
            })

    save_snapshots(current)
    print(f"[SAVED] {len(current)} pages -> {SNAPSHOT_PATH}")

    if is_baseline:
        print("[INFO] Baseline created. No notification sent.")
        sys.exit(0)

    if not changes:
        print("[INFO] No changes detected.")
        sys.exit(0)

    print(f"[INFO] {len(changes)} page(s) changed. Building notifications...")
    notifications = []
    for ch in changes:
        summary = extract_summary(ch["old_text"], ch["new_text"])
        notifications.append({"url": ch["url"], "summary": summary})
        print(f"  -> {ch['url']}")

    message = build_message(notifications)
    send_line_message(message)
    print("[DONE]")


if __name__ == "__main__":
    main()
