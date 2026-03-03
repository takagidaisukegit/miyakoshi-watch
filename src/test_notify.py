"""
LINE通知のテスト用スクリプト。
使い方: python src/test_notify.py
環境変数 LINE_CHANNEL_ACCESS_TOKEN と LINE_USER_ID が必要。
"""
from notifier import send_line_message

message = "[テスト] miyakoshi-watch の通知テストです。LINE連携が正常に機能しています。"
send_line_message(message)
print("テストメッセージを送信しました。")
