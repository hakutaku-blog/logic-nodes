import os
import glob
from gemini_api import generate_text_with_fallback

def rewrite_post(filepath):
    print(f"Rewriting: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        old_content = f.read()

    # ファイル名から日付を抽出
    filename = os.path.basename(filepath)
    date_str = filename[:10] if len(filename) >= 10 else "2026-08-01"

    prompt = f"""
    あなたはテック系ラジオ番組『ハク＆タクのLogic Nodes』の台本ライターです。
    以下の【旧記事のコンテンツ】を元に、対話形式の新しい技術ブログ記事（Markdown形式）として完全に書き換えてください。

    【キャラクター設定と行動ルール】
    - ハク (MC): 読者目線の若手エンジニア。必ず「具体的な技術の仕組み」「既存技術との違い」「現場でのデメリット」など、鋭い技術的な質問を投げかけてください。
    - タク (解説): 経験豊富なシニアエンジニア。ハクの質問に対し、アーキテクチャの背景や専門用語を用いて具体的に解説してください。

    【出力ルール（重要）】
    1. 記事全編を「ハク」と「タク」の対話形式で構成し、技術的な深掘りを行ってください。
    2. タクの解説の中には、必ず「Markdownの表（Table）」または「箇条書き」を使用し、客観的で構造化された技術データを提供してください。
    3. 記事先頭には YAML Frontmatter（title, date, tags, description）を必ず含めてください。
    4. date には必ず元記事と同じ日付 "{date_str}" を YYYY-MM-DD 形式で指定してください。
    5. 最先頭行は直接 `---` で開始してください（```markdown などのコードブロックで囲まないこと）。

    【旧記事のコンテンツ】
    {old_content}
    """

    try:
        new_content, model = generate_text_with_fallback(os.environ.get("GEMINI_API_KEY", ""), prompt)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Success ({model})")
    except Exception as e:
        print(f"Failed to rewrite {filepath}: {e}")

def main():
    post_files = glob.glob("src/posts/*.md")
    for filepath in post_files:
        rewrite_post(filepath)

if __name__ == "__main__":
    main()
