import os
import sys
import glob
import json
import urllib.request
from datetime import datetime, timezone, timedelta
from notify import send_discord_notify
from gemini_api import generate_text_with_fallback

def fetch_tech_trends():
    """海外テックForum（Hacker News）から最新のトップトレンドを自律的に取得する"""
    trends = []
    try:
        print("Fetching latest tech trends from Hacker News...")
        # Hacker Newsのトップ記事IDを取得
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            story_ids = json.loads(response.read().decode('utf-8'))
            
        # 上位3件のタイトルを取得してリスト化
        for sid in story_ids[:3]:
            story_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
            sreq = urllib.request.Request(story_url)
            with urllib.request.urlopen(sreq) as sres:
                story = json.loads(sres.read().decode('utf-8'))
                title = story.get('title', '')
                if title:
                    trends.append(f"・{title}")
    except Exception as e:
        print(f"トレンド取得失敗: {e}")
        trends.append("※最新トレンドの取得に失敗しました。一般的な技術テーマで補完してください。")
        
    return "\n".join(trends)

def update_posts_manifest(output_dir="src/posts"):
    """src/posts 配下の Markdown ファイル一覧を posts.json に保存する"""
    md_files = [os.path.basename(f) for f in glob.glob(os.path.join(output_dir, "*.md")) if f.endswith(".md")]
    md_files.sort(reverse=True)
    manifest_path = os.path.join(output_dir, "posts.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(md_files, f, ensure_ascii=False, indent=2)
    print(f"Updated {manifest_path} with {len(md_files)} posts.")

def update_sitemap_xml(output_dir="src/posts"):
    """sitemap.xml を自動生成・更新する"""
    base_url = "https://hakutaku-blog.github.io/logic-nodes/"
    today_str = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
    md_files = [os.path.basename(f) for f in glob.glob(os.path.join(output_dir, "*.md")) if f.endswith(".md")]
    md_files.sort(reverse=True)
    
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        '  <url>',
        f'    <loc>{base_url}</loc>',
        f'    <lastmod>{today_str}</lastmod>',
        '    <changefreq>daily</changefreq>',
        '    <priority>1.0</priority>',
        '  </url>',
        '  <url>',
        f'    <loc>{base_url}privacy.html</loc>',
        f'    <lastmod>{today_str}</lastmod>',
        '    <changefreq>monthly</changefreq>',
        '    <priority>0.5</priority>',
        '  </url>',
        '  <url>',
        f'    <loc>{base_url}about.html</loc>',
        f'    <lastmod>{today_str}</lastmod>',
        '    <changefreq>monthly</changefreq>',
        '    <priority>0.5</priority>',
        '  </url>'
    ]
    
    for fname in md_files:
        date_str = fname[:10] if len(fname) >= 10 and fname[:4].isdigit() else today_str
        xml_lines.extend([
            '  <url>',
            f'    <loc>{base_url}src/posts/{fname}</loc>',
            f'    <lastmod>{date_str}</lastmod>',
            '    <changefreq>weekly</changefreq>',
            '    <priority>0.8</priority>',
            '  </url>'
        ])
        
    xml_lines.append('</urlset>')
    
    sitemap_path = "sitemap.xml"
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write("\n".join(xml_lines) + "\n")
    print(f"Updated {sitemap_path} with {len(md_files)} URLs.")

def main():
    today_str = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
    output_dir = "src/posts"
    os.makedirs(output_dir, exist_ok=True)
    
    # マニフェストとsitemapの最新化を常に実行
    update_posts_manifest(output_dir)
    update_sitemap_xml(output_dir)
    
    # 1. 二重実行ガード
    existing_files = glob.glob(os.path.join(output_dir, f"*{today_str}*.md"))
    if existing_files:
        print(f"本日の記事は既に生成されています（{existing_files[0]}）。処理を安全にスキップしました。")
        sys.exit(0)

    # 2. APIキーの確認
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        msg = "GEMINI_API_KEYが設定されていません。"
        send_discord_notify(msg, is_error=True)
        sys.exit(1)

    # 3. トレンドの自動巡回・収集（APIを叩く前に実行）
    latest_trends = fetch_tech_trends()

    # 4. 収集したトレンドをAIに渡す動的プロンプトの構築
    prompt = f"""
    あなたはテック系ラジオ番組『ハク＆タクのLogic Nodes』の台本ライターです。
    以下の海外テックトレンドをテーマに、対話形式の技術ブログ記事をMarkdown形式で1つ作成してください。

    【キャラクター設定と行動ルール】
    - ハク (MC): 読者目線の若手エンジニア。必ず「具体的な技術の仕組み」「既存技術との違い」「現場でのデメリット」など、鋭い技術的な質問を投げかけてください。
    - タク (解説): 経験豊富なシニアエンジニア。ハクの質問に対し、アーキテクチャの背景や専門用語を用いて具体的に解説してください。

    【出力ルール（重要）】
    1. 記事全編を「ハク」と「タク」の対話形式で構成し、技術的な深掘りを行ってください。
    2. タクの解説の中には、必ず「Markdownの表（Table）」または「箇条書き」を使用し、客観的で構造化された技術データを提供してください。
    3. 記事先頭には YAML Frontmatter（title, date, tags, description）を必ず含めてください。
    4. date には本日の日付 "{today_str}" を YYYY-MM-DD 形式で指定してください。
    5. 最先頭行は直接 `---` で開始してください（コードブロックで囲まないこと）。

    【本日のトレンドトピック】
    {latest_trends}
    """

    # 5. 記事の生成（フォールバック付き）と保存
    try:
        content, used_model = generate_text_with_fallback(api_key, prompt)

        filename = f"{today_str}-auto-generated.md"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        update_posts_manifest(output_dir)
        update_sitemap_xml(output_dir)
        
        # 記事タイトルのパース
        import re
        title_match = re.search(r'title:\s*["\']?(.*?)["\']?\r?$', content, re.MULTILINE)
        article_title = title_match.group(1) if title_match else filename

        # GA4昨日のアクセス統計取得
        from analytics import fetch_yesterday_ga4_stats
        ga4_stats = fetch_yesterday_ga4_stats()
        if ga4_stats is not None:
            stats_str = f"📊 **昨日のアクセス実績:**\n・ページビュー (PV): **{ga4_stats['page_views']}** PV\n・訪問ユーザー数: **{ga4_stats['active_users']}** 人\n"
        else:
            stats_str = "📊 **昨日のアクセス実績:** （GA4 APIデータ取得中）\n"

        msg = f"📝 **本日更新の記事:**\n「{article_title}」\n\n" \
              f"{stats_str}\n" \
              f"🤖 **使用モデル:** {used_model}\n" \
              f"📁 **保存先:** `{filepath}`\n\n" \
              f"【収集したトレンド】\n{latest_trends}"
        
        print(msg)
        send_discord_notify(msg, is_error=False)

    except Exception as e:
        msg = f"API実行中にエラーが発生し、フォールバックも失敗しました。\n詳細: {e}"
        print(msg)
        send_discord_notify(msg, is_error=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

