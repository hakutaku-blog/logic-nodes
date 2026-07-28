import os
import sys
import json
import urllib.request
from datetime import datetime

def send_discord_notify(message, is_error=False):
    """Discordへ通知を送信する関数"""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("Discord Webhook URLが設定されていません。")
        return
    
    color = 16711680 if is_error else 65280
    payload = {
        "embeds": [{
            "title": "🔍 APIモデル調査ツール",
            "description": message,
            "color": color
        }]
    }
    
    req = urllib.request.Request(webhook_url, method="POST")
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) logic-nodes/1.0')
    
    try:
        urllib.request.urlopen(req, data=json.dumps(payload).encode('utf-8'))
    except Exception as e:
        print(f"Discord通知失敗: {e}")

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        msg = "GEMINI_API_KEYが設定されていません。"
        print(msg)
        send_discord_notify(msg, is_error=True)
        sys.exit(1)

    try:
        print("Fetching available models via REST API...")
        # SDKを使わず、GoogleのAPIエンドポイントを直接叩いて確実なリストを取得
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        req = urllib.request.Request(url)
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        available_models = [model.get("name") for model in data.get("models", []) if "name" in model]
        
        if not available_models:
            msg = "利用可能なモデルが見つかりませんでした。"
            print(msg)
            send_discord_notify(msg, is_error=True)
            sys.exit(1)
        
        model_list_str = "\n".join(available_models)
        
        # Discordの文字数制限対策
        if len(model_list_str) > 1900:
            model_list_str = model_list_str[:1900] + "\n... (省略)"
            
        msg = f"現在のAPIキーで利用可能なモデル一覧:\n```text\n{model_list_str}\n```\nこのリスト内にある名前が、確実に使用可能なモデルです。"
        print(msg)
        send_discord_notify(msg, is_error=False)
        
        sys.exit(0)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        msg = f"HTTP Error {e.code}: {e.reason}\n詳細: {error_body}"
        print(msg)
        send_discord_notify(msg, is_error=True)
        sys.exit(1)
    except Exception as e:
        error_msg = str(e)
        msg = f"モデル一覧の取得中にエラーが発生しました。\n詳細: {error_msg}"
        print(msg)
        send_discord_notify(msg, is_error=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
