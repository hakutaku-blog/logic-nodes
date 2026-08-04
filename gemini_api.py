import os
from google import genai

# Google AI Studioのアクティブ推奨モデル
PREFERRED_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

def generate_text_with_fallback(api_key, prompt, preferred_model="gemini-2.0-flash"):
    """
    安定した推奨モデルでコンテンツを生成する。
    API制限（429等）発生時はクォータ消費を防ぐため無理に連投せず、翌日の自動更新へ安全に引き継ぐ。
    """
    client = genai.Client(api_key=api_key)
    
    models_to_try = [preferred_model] if preferred_model else []
    for m in PREFERRED_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

    errors = []
    for model_name in models_to_try:
        try:
            print(f"Generating content using model: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response and response.text:
                print(f"Successfully generated content using {model_name}")
                return response.text, model_name
        except Exception as e:
            err_str = str(e)
            print(f"Model {model_name} failed: {err_str}")
            errors.append(f"{model_name}: {err_str}")

    raise RuntimeError(f"API利用制限または一時エラーが発生しました。クォータリセット後（翌日）の自動投稿で再開されます。\n詳細:\n" + "\n".join(errors))
