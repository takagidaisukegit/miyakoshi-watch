"""
E2Eテスト: ホームページの更新検知からLINE通知までの流れをテストする。

テスト方法:
  1. 実際にサイトをクロール（1ページ）して「現在のハッシュ」を取得
  2. 旧スナップショットのハッシュを別の値に差し替えて「サイトが更新された」状態を再現
  3. main.py と完全に同一のハッシュ比較ロジックで変更を検知
  4. LINEに通知を送信

注意: snapshots.json は書き換えない。本番の監視には影響なし。
"""
from scraper import crawl
from differ import extract_summary
from notifier import send_line_message, build_message

TARGET_URL = "https://www.miyakoshi-holdings.com"
FAKE_OLD_HASH = "0" * 64  # 実際のハッシュとは必ず一致しない値


def main():
    print("[E2E] 現在のページを取得中...")
    current = crawl(base_url=TARGET_URL, max_pages=1)
    if not current:
        print("[E2E ERROR] クロール失敗")
        return

    url = list(current.keys())[0]
    print(f"[E2E] 対象URL: {url}")

    # ---- 旧スナップショットを偽装 ----
    # 旧ハッシュを別の値にすることで「前回からサイトが更新された」状態を再現する
    old_snapshots = {
        url: {
            "hash": FAKE_OLD_HASH,
            "text": "(E2Eテスト: このURLは以前別のコンテンツを持っていた)",
        }
    }

    # ---- main.py と完全に同一の変更検知ロジック ----
    changes = []
    for u, data in current.items():
        if u not in old_snapshots:
            continue
        if old_snapshots[u]["hash"] != data["hash"]:
            print(f"[E2E] 変更検知: {u}")
            changes.append({
                "url": u,
                "old_text": old_snapshots[u]["text"],
                "new_text": data["text"],
            })

    if not changes:
        print("[E2E ERROR] 変更が検知されませんでした（ロジックに問題がある可能性）")
        return

    # ---- 通知送信 ----
    notifications = []
    for ch in changes:
        summary = extract_summary(ch["old_text"], ch["new_text"])
        notifications.append({"url": ch["url"], "summary": summary})

    message = "[E2Eテスト]\n" + build_message(notifications)
    print(f"[E2E] 送信内容:\n{message}")
    send_line_message(message)
    print("[E2E] 完了。LINEを確認してください。")


if __name__ == "__main__":
    main()
