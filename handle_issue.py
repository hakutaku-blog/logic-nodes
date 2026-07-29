import os
import sys
import json
import urllib.request
from notify import send_discord_notify
from gemini_api import generate_text_with_fallback

def reply_to_github_issue(issue_number, comment_body, token):
    """GitHub Issue にコメントを返信する"""
    repo = os.environ.get("GITHUB_REPOSITORY", "hakutaku-blog/logic-nodes")
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    
    req = urllib.request.Request(url, method="POST")
    req.add_header('Authorization', f'token {token}')
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0 logic-nodes-issue-bot')
    
    payload = {"body": comment_body}
    try:
        with urllib.request.urlopen(req, data=json.dumps(payload).encode('utf-8')) as res:
            print(f"Replied to Issue #{issue_number}: {res.getcode()}")
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

    if not issue:
        print("No issue found in event.")
        sys.exit(0)

    issue_number = issue.get("number")
    issue_title = issue.get("title", "")
    issue_body = issue.get("body", "")
    html_url = issue.get("html_url", "")
    user_login = issue.get("user", {}).get("login", "ゲスト")

    api_key = os.environ.get("GEMINI_API_KEY")
    github_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_PAT")

    print(f"Processing Issue #{issue_number}: {issue_title} by {user_login}")

    prompt = f"""
    あなたは技術ブログ「Logic-Nodes」の公式AIアシスタントです。
    読者またはユーザーから以下の問い合わせ（GitHub Issue）が届きました。
    丁寧、親切、かつ技術的に正確で分かりやすい返信コメントを日本語で作成してください。

    【問い合わせタイトル】
    {issue_title}

    【問い合わせ本文】
    {issue_body}

    【最新コメント（あれば）】
    {comment.get('body', '') if comment else 'なし'}

    【返信のルール】
    1. 感謝の言葉から始めてください。
    2. 質問やご意見に対して的確な回答や対応方針を述べてください。
    3. 必要に応じて「Logic-Nodes 運営チームにて順次確認・対応いたします」と添えてください。
    """

    try:
        ai_reply, used_model = generate_text_with_fallback(api_key, prompt)
        footer = "\n\n---\n*※このコメントは Logic-Nodes の AI サポートアシスタントにより自動生成・返信されました。*"
        full_reply = ai_reply + footer

        if github_token:
            reply_to_github_issue(issue_number, full_reply, github_token)

        # Discord への通知
        discord_msg = f"📩 **新しいお問い合わせ（Issue #{issue_number}）を受信し、AIが自動返信しました！**\n\n" \
                      f"👤 **投稿者:** {user_login}\n" \
                      f"📌 **タイトル:** {issue_title}\n" \
                      f"🔗 **URL:** {html_url}\n\n" \
                      f"🤖 **AI返信:**\n```\n{ai_reply[:300]}...\n```"
        
        send_discord_notify(discord_msg, is_error=False)

    except Exception as e:
        print(f"Error handling issue: {e}")
        send_discord_notify(f"❌ Issue #{issue_number} の自動返信処理中にエラーが発生しました: {e}", is_error=True)

if __name__ == "__main__":
    main()
