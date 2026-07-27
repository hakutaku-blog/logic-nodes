import os
import sys
from datetime import datetime
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY is not set.")
    sys.exit(1)

client = genai.Client()
today = datetime.now().strftime("%Y-%m-%d")

prompt = f"""
あなたは「Logic-Nodes」のAI技術ライターです。
本日の日付: {today}

エンジニア向けに、最新のAIツール（Cursor, MCP, LLM API等）やインフラ・CI/CDに関する
「現場で役に立つ地雷回避・実践ハック」をテーマにしたMarkdown形式の技術記事を執筆してください。

【構成要件】
- Frontmatter（title, date, tagsなど）を先頭に含めること
- 読者がすぐに試せる具体的な設定例やコードブロックを含めること
- 導入、問題の背景、解決策、まとめの構成にすること
"""

# 優先モデルのリスト（最新の2.5-flashから順にテスト）
candidate_models = [
    'gemini-2.5-flash',
    'gemini-2.0-flash',
    'gemini-1.5-flash',
]

response = None
used_model = None

# まず優先リストで生成を試行
for m in candidate_models:
    try:
        print(f"Trying model: {m}...")
        response = client.models.generate_content(
            model=m,
            contents=prompt,
        )
        used_model = m
        print(f"Success with model: {m}")
        break
    except Exception as e:
        print(f"Model {m} failed: {e}")

# もし優先リストが全滅した場合、アカウントで利用可能な全モデルを自動検出してフォールバック
if not response:
    print("Fallback: Searching available models dynamically...")
    try:
        for m in client.models.list():
            if "generateContent" in getattr(m, "supported_generation_methods", []) or "flash" in m.name:
                try:
                    print(f"Trying fallback model: {m.name}...")
                    response = client.models.generate_content(
                        model=m.name,
                        contents=prompt,
                    )
                    used_model = m.name
                    print(f"Success with fallback model: {m.name}")
                    break
                except Exception as inner_e:
                    print(f"Fallback model {m.name} failed: {inner_e}")
    except Exception as list_e:
        print(f"Failed to list models: {list_e}")

if not response or not response.text:
    print("CRITICAL ERROR: All models failed to generate content.")
    sys.exit(1)

os.makedirs("src/posts", exist_ok=True)
filename = f"src/posts/{today}-auto-article.md"

with open(filename, "w", encoding="utf-8") as f:
    f.write(response.text)

print(f"Successfully generated article using [{used_model}]: {filename}")
