import os
import json
from google import genai

BLACKLIST_FILE = "src/posts/model_blacklist.json"

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

def generate_text_with_fallback(api_key, prompt, preferred_model=None):
    """
    APIから利用可能なモデルを動的取得し、自己学習型ブラックリストで無効モデルを弾いてフォールバック生成する。
    """
    client = genai.Client(api_key=api_key)
    blacklist = load_blacklist()
    
    dynamic_models = []
    try:
        # APIから利用可能なモデル一覧を動的取得
        for m in client.models.list_models():
            # generateContent をサポートしているモデルのみを抽出
            if m.supported_generation_methods and "generateContent" in m.supported_generation_methods:
                name = m.name.replace("models/", "")
                dynamic_models.append(name)
    except Exception as e:
        print(f"Failed to fetch model list: {e}")
        # 動的取得自体が失敗した場合の最低限のフォールバック
        dynamic_models = ["gemini-3.6-flash", "gemini-3.5-flash"]
        
    # モデル名を降順にソート（バージョン番号が大きい＝新しいモデルから優先的に試すため）
    # 例: gemini-3.6-flash -> gemini-3.5-flash -> gemini-2.5-flash
    dynamic_models.sort(reverse=True)

    models_to_try = []
    if preferred_model and preferred_model not in models_to_try:
        models_to_try.append(preferred_model)
    
    for dm in dynamic_models:
        if dm not in models_to_try:
            models_to_try.append(dm)

    # ブラックリストに載っているモデルを完全に除外
    models_to_try = [m for m in models_to_try if m not in blacklist]
    
    if not models_to_try:
        raise RuntimeError("利用可能なすべてのモデルがブラックリストに登録されています。")

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
            
            # 致命的エラー（404, 400, limit:0 など）を検知した場合、ブラックリストに追加
            if "404" in err_str or "400" in err_str or ("429" in err_str and "limit: 0" in err_str):
                blacklist[model_name] = f"Banned due to: {err_str.splitlines()[0]}"
                blacklist_updated = True
                errors.append(f"{model_name}: 永続的エラーのためブラックリストへ追加しました")
            else:
                # 一時的なエラーの場合はブラックリストには入れず、エラーを記録して終了する（ルール3）
                errors.append(f"{model_name}: 一時的なエラー ({err_str.splitlines()[0]})")
                break 

    if blacklist_updated:
        save_blacklist(blacklist)

    raise RuntimeError(f"APIエラーまたは利用制限が発生しました。\n詳細:\n" + "\n".join(errors))
