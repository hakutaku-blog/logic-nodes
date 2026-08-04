import os
from google import genai

# 確実に動作する推奨モデルのフォールバック優先順位リスト
PREFERRED_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-8b"
]

def generate_text_with_fallback(api_key, prompt, preferred_model="gemini-2.0-flash"):
    """
    推奨モデルリストを順番に試行し、エラー発生時は次の安定モデルへ自動フォールバックする
    """
    client = genai.Client(api_key=api_key)
    
    models_to_try = []
    if preferred_model:
        models_to_try.append(preferred_model)
    
    for m in PREFERRED_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

    errors = []
    for model_name in models_to_try:
        try:
            print(f"Trying model: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response and response.text:
                print(f"Successfully generated content using {model_name}")
                return response.text, model_name
        except Exception as e:
            err_msg = f"{model_name}: {e}"
            print(f"Model {model_name} failed: {err_msg}")
            errors.append(err_msg)

    raise RuntimeError(f"すべての代替モデルでの生成に失敗しました。\nエラー詳細:\n" + "\n".join(errors))
