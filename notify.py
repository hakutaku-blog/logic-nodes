import os
import json
import urllib.request

def send_discord_notify(message, is_error=False):
    """Discordへ通知を送信する"""
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
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) logic-nodes/1.0')
    
    try:
        urllib.request.urlopen(req, data=json.dumps(payload).encode('utf-8'))
    except Exception as e:
        print(f"Discord通知失敗: {e}")
