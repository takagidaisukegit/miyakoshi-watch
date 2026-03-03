import difflib

MAX_ADDED_LINES = 10
MAX_SUMMARY_CHARS = 400


def extract_summary(old_text: str, new_text: str) -> str:
    """
    変更前後のテキストを比較し、追加された行を抽出して要約文字列を返す。
    difflib.unified_diff を使用（完全無料）。
    """
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    added_lines = []
    removed_lines = []

    diff = difflib.unified_diff(old_lines, new_lines, lineterm="")
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            text = line[1:].strip()
            if text:
                added_lines.append(text)
        elif line.startswith("-") and not line.startswith("---"):
            text = line[1:].strip()
            if text:
                removed_lines.append(text)

    parts = []
    if added_lines:
        added_sample = "\n".join(added_lines[:MAX_ADDED_LINES])
        parts.append(f"追加:\n{added_sample}")
    if removed_lines:
        removed_sample = "\n".join(removed_lines[:5])
        parts.append(f"削除:\n{removed_sample}")

    summary = "\n".join(parts) if parts else "変更が検出されましたが、差分の抽出に失敗しました。"
    if len(summary) > MAX_SUMMARY_CHARS:
        summary = summary[:MAX_SUMMARY_CHARS] + "..."
    return summary
