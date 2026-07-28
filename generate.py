import os
import sys
import glob
from datetime import datetime
from notify import send_discord_notify
from gemini_api import generate_text_with_fallback

def main():
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # 保存先ディレクトリの指定（なければ作成）
    output_dir = "src/posts"
    os.makedirs(output_dir, exist_ok=True)
    
    # 検索先も src/posts 内に変更
    existing_files = glob.glob(os.path.join(output_dir, f"*{today_str}*.md"))
    
    # 1. 二重実行ガード
    if existing_files:
        msg = f"本日の記事は既に生成されています（{existing_files[0]}）。処理を安全にスキップしました。"
        print(msg)
        send_discord_notify(msg, is_error=False)
        sys.exit(0)

    # 2. APIキーの確認
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        msg = "GEMINI_API_KEYが設定されていません。"
        send_discord_notify(msg, is_error=True)
        sys.exit(1)

    prompt = """
    フロントエンド、DevOps、AIエディタ（CursorやMCP等）に関する最新の技術ブログ記事をMarkdown形式で1つ作成してください。
    YAML Frontmatter（title, date, tags, description）を含めてください。
    """

    # 3. 記事の生成（フォールバック付き）と保存
    try:
        content, used_model = generate_text_with_fallback(api_key, prompt)

        # 保存先パスを src/posts/ 配下に変更
        filename = f"{today_str}-auto-generated.md"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        msg = f"記事の生成に成功しました！\n使用モデル: {used_model}\nファイル名: {filepath}"
        print(msg)
        send_discord_notify(msg, is_error=False)

    except Exception as e:
        msg = f"API実行中にエラーが発生し、フォールバックも失敗しました。\n詳細: {e}"
        print(msg)
        send_discord_notify(msg, is_error=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
