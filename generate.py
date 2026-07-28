import os
import sys
import json
import urllib.request
from google import genai
from datetime import datetime
import glob

def send_discord_notify(message, is_error=False):
    """Discordへ通知を送信する関数"""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("Discord Webhook URLが設定されていません。")
        return
    
    color = 16711680 if is_error else 65280
    payload = {
        "embeds": [{
            "title": "❌ ブログ自動更新エラー" if is_error else "✅ ブログ自動更新完了",
            "description": message,
            "color": color
        }]
    }
    
    req = urllib.request.Request(webhook_url, method="POST")
    req.add_header('Content-Type', 'application/json')
    # 【403エラー対策】Discordに弾かれないようUser-Agentを追加
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) logic-nodes/1.0')
    
    try:
        urllib.request.urlopen(req, data=json.dumps(payload).encode('utf-8'))
    except Exception as e:
        print(f"Discord通知失敗: {e}")

def main():
    today_str = datetime.now().strftime("%Y-%m-%d")
    existing_files = glob.glob(f"*{today_str}*.md")
    
    if existing_files:
        msg = f"本日の記事は既に生成されています（{existing_files[0]}）。処理を安全にスキップしました。"
        print(msg)
        send_discord_notify(msg, is_error=False)
        sys.exit(0)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        msg = "GEMINI_API_KEYが設定されていません。"
        send_discord_notify(msg, is_error=True)
        sys.exit(1)

    prompt = """
    フロントエンド、DevOps、AIエディタ（CursorやMCP等）に関する最新の技術ブログ記事をMarkdown形式で1つ作成してください。
    YAML Frontmatter（title, date, tags, description）を含めてください。
    """

    try:
        print("Generating content using model: gemini-2.5-flash...")
        # 【警告対策】最新の google-genai SDK の記述方式に変更
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        content = response.text

        filename = f"{today_str}-auto-generated.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        
        msg = f"記事の生成に成功しました！\nファイル名: {filename}"
        print(msg)
        send_discord_notify(msg, is_error=False)

    except Exception as e:
        error_msg = str(e)
        msg = f"API実行中にエラーが発生しました。\n詳細: {error_msg}"
        print(msg)
        send_discord_notify(msg, is_error=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
