import os
import sys
import json
import urllib.request
from notify import send_discord_notify

def reply_to_github_issue(issue_number, comment_body, token):
    """GitHub Issue に定型確認コメントを返信する（API非消費）"""
    repo = os.environ.get("GITHUB_REPOSITORY", "hakutaku-blog/logic-nodes")
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    
    req = urllib.request.Request(url, method="POST")
    req.add_header('Authorization', f'token {token}')
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0 logic-nodes-issue-bot')
    
    payload = {"body": comment_body}
    try:
        with urllib.request.urlopen(req, data=json.dumps(payload).encode('utf-8')) as res:
            print(f"Replied static message to Issue #{issue_number}: {res.getcode()}")
    except Exception as e:
        print(f"Failed to post comment to Issue #{issue_number}: {e}")

def main():
    # GitHub Actions のイベントペイロード取得
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path or not os.path.exists(event_path):
        print("No event path found. Exiting.")
        sys.exit(0)

    with open(event_path, "r", encoding="utf-8") as f:
        event = json.load(f)

    issue = event.get("issue")
    action = event.get("action")
    comment = event.get("comment")

    # Bot自身の投稿による無限ループ防止
    sender = event.get("sender", {}).get("login", "")
    if sender.endswith("[bot]") or sender == "github-actions[bot]":
        print("Event triggered by bot. Skipping.")
        sys.exit(0)

    # 新規作成(opened)以外は無視してAPI/通知を節約
    if action != "opened" or not issue:
        print(f"Action '{action}' ignored.")
        sys.exit(0)

    issue_number = issue.get("number")
    issue_title = issue.get("title", "")
    issue_body = issue.get("body", "")
    html_url = issue.get("html_url", "")
    user_login = issue.get("user", {}).get("login", "ゲスト")

    github_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_PAT")

    # 1. 定型の自動受領コメント（Gemini API消費ゼロ）
    static_reply = "お問い合わせありがとうございます！メッセージを受信いたしました。運営者（Logic-Nodes管理チーム）にて内容を確認次第、対応させていただきます。"
    if github_token:
        reply_to_github_issue(issue_number, static_reply, github_token)

    # 2. Discord への即時通知（Gemini API消費ゼロ）
    discord_msg = f"📩 **新しいお問い合わせ（Issue #{issue_number}）が届きました！**\n\n" \
                  f"👤 **投稿者:** {user_login}\n" \
                  f"📌 **タイトル:** {issue_title}\n" \
                  f"🔗 **URL:** {html_url}\n\n" \
                  f"📝 **内容:**\n```\n{issue_body[:300]}\n```"
    
    send_discord_notify(discord_msg, is_error=False)

if __name__ == "__main__":
    main()
