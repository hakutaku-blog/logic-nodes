import os
import sys
import json
import urllib.request
import google.generativeai as genai
from datetime import datetime
import glob
import time

def send_discord_notify(message, is_error=False):
    """Discordへ通知を送信する関数"""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("Discord Webhook URLが設定されていません。")
        return
    
    color = 16711680 if is_error else 65280 # エラーは赤、成功は緑
    payload = {
        "embeds": [{
            "title": "❌ ブログ自動更新エラー" if is_error else "✅ ブログ自動更新完了",
            "description": message,
            "color": color
        }]
    }
    
    req = urllib.request.Request(webhook_url, method="POST")
    req.add_header('Content-Type', 'application/json')
    try:
        urllib.request.urlopen(req, data=json.dumps(payload).encode('utf-8'))
    except Exception as e:
        print(f"Discord通知失敗: {e}")

def main():
    # 1. 二重実行ガード（本日の記事が既に存在するかチェック）
    today_str = datetime.now().strftime("%Y-%m-%d")
    existing_files = glob.glob(f"*{today_str}*.md")
    
    if existing_files:
        msg = f"本日の記事は既に生成されています（{existing_files[0]}）。処理を安全にスキップしました。"
        print(msg)
        # 通知がうるさければ、スキップ時は通知しないようにコメントアウトしてもOKです
        send_discord_notify(msg, is_error=False)
        sys.exit(0)

    # 2. Gemini APIのセットアップと実行
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        msg = "GEMINI_API_KEYが設定されていません。"
        send_discord_notify(msg, is_error=True)
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')

    prompt = """
    フロントエンド、DevOps、AIエディタ（CursorやMCP等）に関する最新の技術ブログ記事をMarkdown形式で1つ作成してください。
    YAML Frontmatter（title, date, tags, description）を含めてください。
    """

    try:
        print("Generating content using model: gemini-2.0-flash...")
        response = model.generate_content(prompt)
        content = response.text

        # ファイル保存
        filename = f"{today_str}-auto-generated.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        
        msg = f"記事の生成に成功しました！\nファイル名: {filename}"
        print(msg)
        send_discord_notify(msg, is_error=False)

    except Exception as e:
        error_msg = str(e)
        # 無駄なリトライを廃止し、即時Failさせる
        msg = f"API実行中にエラーが発生しました。\n詳細: {error_msg}"
        print(msg)
        send_discord_notify(msg, is_error=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
