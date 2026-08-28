import os
import sys
import glob
import json
import urllib.request
import re
from datetime import datetime, timezone, timedelta
from notify import send_discord_notify
from gemini_api import generate_text_with_fallback

def fetch_tech_trends():
    """海外テックForum（Hacker News）から最新のトップトレンドとトップコメントを取得する"""
    trends = []
    import html
    try:
        print("Fetching latest tech trends and comments from Hacker News...")
        # Hacker Newsのトップ記事IDを取得
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            story_ids = json.loads(response.read().decode('utf-8'))
            
        # 上位2件のタイトルとコメントを取得してリスト化
        for sid in story_ids[:2]:
            story_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
            sreq = urllib.request.Request(story_url)
            with urllib.request.urlopen(sreq) as sres:
                story = json.loads(sres.read().decode('utf-8'))
                title = story.get('title', '')
                kids = story.get('kids', [])
                if not title:
                    continue
                
                trend_text = f"【テーマ】: {title}\n"
                
                # トップ3件のコメントを取得
                comments = []
                for kid_id in kids[:3]:
                    kid_url = f"https://hacker-news.firebaseio.com/v0/item/{kid_id}.json"
                    try:
                        kreq = urllib.request.Request(kid_url)
                        with urllib.request.urlopen(kreq) as kres:
                            kid_data = json.loads(kres.read().decode('utf-8'))
                            if kid_data and 'text' in kid_data and not kid_data.get('deleted'):
                                c_text = html.unescape(kid_data['text'])
                                c_text = re.sub(r'<[^>]+>', ' ', c_text) # HTMLタグ除去
                                if len(c_text) > 300:
                                    c_text = c_text[:300] + "..."
                                comments.append(f"- 現場の声: {c_text}")
                    except Exception:
                        pass
                
                if comments:
                    trend_text += "【世界中のエンジニアのリアルな声（賛否両論）】:\n" + "\n".join(comments) + "\n"
                
                trends.append(trend_text)
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
    target_date = os.environ.get("TARGET_DATE", "").strip()
    if target_date:
        today_str = target_date
    else:
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

    # 4. 今日のトレンドをAIに渡すプロンプトの構築
    prompt = f"""
    あなたはトップクラスのテックブログ編集者です。
    以下の海外テックトレンド（Hacker Newsの記事と実際の開発者からの賛否両論コメント）を元に、対話形式の技術ブログ記事をMarkdown形式で作成してください。

    【制約事項：E-E-A-Tと読者価値の担保（AdSense対策）】
    1. 単なる翻訳や要約は絶対に行わず、必ず「実務的トレードオフ分析（弁証法）」を行ってください。
    2. ハク（野心的なイノベーター）の役割: 最新技術の「可能性・メリット・開発者体験の向上」を熱く語る。
    3. タク（歴戦のSRE・実務家）の役割: HNのリアルな声に基づき、「本番環境でのリスク・技術的負債・エッジケース・代替手段との比較」をプロの視点で鋭く指摘する。
    4. 以下の【厳格な出力テンプレート】に従い、必ず `---` で囲まれたYAML Frontmatterを先頭に出力してください。他の形式や余計な挨拶は一切禁止します。

    【厳格な出力テンプレート】
    ---
    title: "記事のメインテーマ（ラジオ番組名は含めず、〇〇技術の台頭と現場導入へのハードル のように端的に）"
    date: "{today_str}"
    tags: ["Tech", "タグ2", "タグ3"]
    description: "記事の要約を1文で"
    ---

    ## 1. [見出し1]

    **ハク**: みなさんこんにちは！テック系ラジオ『ハク＆タクのLogic Nodes』の時間です。MCのハクです！

    （以下、ハクとタクの弁証法的な対話）

    ## 結論：ユースケース診断（現場で採用すべきケース/見送るべきケース）
    - 採用すべきケース: ...
    - 見送るべきケース: ...

    【本日のトレンドトピックと現場のリアルな声】
    {latest_trends}
    """

    # 5. 記事の生成（フォールバック付き）と保存
    try:
        content, used_model = generate_text_with_fallback(api_key, prompt)

        # 出力結果のサニタイズ処理と通知用ログの記録
        sanitize_logs = []

        # 【対策1】Markdownフェンスの強制除去
        if re.search(r'^```(?:markdown)?\s*', content) or re.search(r'\s*```$', content):
            content = re.sub(r'^```(?:markdown)?\s*', '', content)
            content = re.sub(r'\s*```$', '', content)
            sanitize_logs.append("Markdownフェンス（```）を検知し、自動除去しました")

        # 【対策2】おしゃべりテキスト（Chatty Assistant）の強制切除
        match = re.search(r'^---$', content, flags=re.MULTILINE)
        if match and match.start() > 0:
            content = content[match.start():]
            sanitize_logs.append("不要な挨拶テキストを検知し、Frontmatter開始位置まで切除しました")

        # 【対策3】ハルシネーション（架空エピソード番号）の除去
        if re.search(r'(Logic Nodes)\s*(?:#|第|Vol\.?)\s*\d+\s*(?:回)?', content, flags=re.IGNORECASE):
            content = re.sub(r'(Logic Nodes)\s*(?:#|第|Vol\.?)\s*\d+\s*(?:回)?', r'\1', content, flags=re.IGNORECASE)
            sanitize_logs.append("架空のエピソード番号（ハルシネーション）を検知し、自動除去しました")

        filename = f"{today_str}-auto-generated.md"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        update_posts_manifest(output_dir)
        update_sitemap_xml(output_dir)
        
        # 記事タイトルのパース
        title_match = re.search(r'title:\s*["\']?(.*?)["\']?\r?$', content, re.MULTILINE)
        article_title = title_match.group(1) if title_match else filename

        # GA4昨日のアクセス統計取得
        from analytics import fetch_yesterday_ga4_stats
        ga4_stats = fetch_yesterday_ga4_stats()
        if ga4_stats is not None:
            stats_str = f"📊 **昨日のアクセス実績:**\n・ページビュー (PV): **{ga4_stats['page_views']}** PV\n・訪問ユーザー数: **{ga4_stats['active_users']}** 人\n"
        else:
            stats_str = "📊 **昨日のアクセス実績:** （GA4 APIデータ取得中）\n"

        msg = f"✅ **本日の更新完了:**\n「{article_title}」\n\n" \
              f"{stats_str}\n" \
              f"🤖 **使用モデル:** {used_model}\n" \
              f"📁 **保存先:** `{filepath}`\n\n" \
              f"【取得したトレンド】\n{latest_trends}"
        
        if sanitize_logs:
            msg += "\n\n**【⚙️ 自動サニタイズ実行レポート】**\n" + "\n".join(f"- {log}" for log in sanitize_logs)
            msg += "\n*※AIの出力ブレを検知し、システムが自動補正しました。*"

        print(msg)
        send_discord_notify(msg, is_error=False)

    except Exception as e:
        msg = f"API実行中にエラーが発生し、フォールバックも失敗しました。\n詳細: {e}"
        print(msg)
        send_discord_notify(msg, is_error=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

