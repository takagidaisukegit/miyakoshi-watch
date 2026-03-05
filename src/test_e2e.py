"""
E2Eテスト: サイトをクロールし、変更検知からLINE通知までの一連の流れをテストする。
snapshots.json を書き換える必要はなく、擬似的な「旧テキスト」を使って差分を生成する。
"""
from scraper import crawl
from differ import extract_summary
from notifier import send_line_message, build_message

TEST_URL = "https://www.miyakoshi-holdings.com"


def main():
    print("[E2E] メインページをクロール中...")
    current = crawl(base_url=TEST_URL, max_pages=1)

    if not current:
        print("[E2E ERROR] クロール失敗")
        return

    url = list(current.keys())[0]
    new_text = current[url]["text"]

    # 旧テキストを空文字にして必ず差分が生じるようにする
    fake_old_text = "(旧バージョン: テスト用のダミーテキスト)"

    summary = extract_summary(fake_old_text, new_text)
    notifications = [{"url": url, "summary": summary}]

    message = build_message(notifications)
    message = "[E2Eテスト]\n" + message

    print(f"[E2E] LINE通知送信中...\n---\n{message}\n---")
    send_line_message(message)
    print("[E2E] 完了。LINEに通知が届いているか確認してください。")


if __name__ == "__main__":
    main()
