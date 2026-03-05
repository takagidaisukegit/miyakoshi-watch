import base64
import json
import os
import sys
import urllib.error
import urllib.request
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


def push_snapshots_to_github(data: dict) -> None:
    """GitHub API経由でsnapshots.jsonを直接更新（git push不要）"""
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")

    print(f"[API] GITHUB_TOKEN set: {bool(token)}, GITHUB_REPOSITORY: {repo!r}")

    if not token or not repo:
        print("[API] WARN: env vars missing, skipping GitHub update")
        return

    content = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    url = f"https://api.github.com/repos/{repo}/contents/data/snapshots.json"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github+json",
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            file_info = json.loads(resp.read())
            current_sha = file_info["sha"]
        print(f"[API] current sha: {current_sha[:7]}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[API] ERROR getting file SHA: {e.code} {body}")
        raise

    try:
        payload = json.dumps({
            "message": "chore: update snapshots [skip ci]",
            "content": base64.b64encode(content).decode(),
            "sha": current_sha,
        }).encode()
        req = urllib.request.Request(url, data=payload, headers=headers, method="PUT")
        with urllib.request.urlopen(req) as resp:
            print(f"[API] snapshots.json updated: {resp.status}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[API] ERROR updating file: {e.code} {body}")
        raise


def main():
    print("[START] crawling...")
    current = crawl()

    old_snapshots = load_snapshots()
    is_baseline = len(old_snapshots) == 0

    changes = []
    for url, data in current.items():
        if url not in old_snapshots:
            if not is_baseline:
                print(f"[NEW PAGE] {url}")
                changes.append({
                    "url": url,
                    "old_text": "",
                    "new_text": data["text"],
                })
            continue
        if old_snapshots[url]["hash"] != data["hash"]:
            print(f"[CHANGED] {url}")
            changes.append({
                "url": url,
                "old_text": old_snapshots[url]["text"],
                "new_text": data["text"],
            })

    save_snapshots(current)
    push_snapshots_to_github(current)
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
