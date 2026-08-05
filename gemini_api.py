import os
import json
from google import genai

BLACKLIST_FILE = "src/posts/model_blacklist.json"

# 無料枠でも利用可能な可能性が高い順、または安定順
PREFERRED_MODELS = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.5-flash",
]

def load_blacklist():
    if os.path.exists(BLACKLIST_FILE):
        try:
            with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_blacklist(blacklist):
    os.makedirs(os.path.dirname(BLACKLIST_FILE), exist_ok=True)
    with open(BLACKLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(blacklist, f, ensure_ascii=False, indent=2)

def generate_text_with_fallback(api_key, prompt, preferred_model="gemini-1.5-flash"):
    """
    自己学習型ブラックリストを用いたフォールバック生成。
    404 や 429 limit: 0 の永続的エラーが出たモデルは外部ファイルに記録し、以後のリクエストをブロックする。
    """
    client = genai.Client(api_key=api_key)
    blacklist = load_blacklist()
    
    models_to_try = [preferred_model] if preferred_model else []
    for m in PREFERRED_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

    # ブラックリストに載っているモデルを除外
    models_to_try = [m for m in models_to_try if m not in blacklist]
    
    if not models_to_try:
        raise RuntimeError("利用可能なすべてのモデルがブラックリストに登録されています。APIキーの有効性やプランを確認してください。")

    errors = []
    blacklist_updated = False

    for model_name in models_to_try:
        try:
            print(f"Generating content using model: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response and response.text:
                print(f"Successfully generated content using {model_name}")
                if blacklist_updated:
                    save_blacklist(blacklist)
                return response.text, model_name
        except Exception as e:
            err_str = str(e)
            print(f"Model {model_name} failed: {err_str}")
            
            # 致命的エラー（404 または 429 limit: 0）を検知した場合、ブラックリストに追加
            if "404" in err_str or ("429" in err_str and "limit: 0" in err_str):
                blacklist[model_name] = f"Banned due to: {err_str.splitlines()[0]}"
                blacklist_updated = True
                errors.append(f"{model_name}: 永続的エラー(404/limit:0)のためブラックリストへ追加しました")
            else:
                # 一時的なエラーの場合はブラックリストには入れず、エラーを記録して終了する（ルール3）
                errors.append(f"{model_name}: 一時的なエラー ({err_str.splitlines()[0]})")
                break # 一時的エラーは翌日回復を待つためフォールバックせずに終了

    if blacklist_updated:
        save_blacklist(blacklist)

    raise RuntimeError(f"APIエラーまたは利用制限が発生しました。\n詳細:\n" + "\n".join(errors))
