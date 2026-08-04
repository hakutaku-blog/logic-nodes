import os
import time
from google import genai

# Google AI Studioのアクティブ推奨モデル
PREFERRED_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

def generate_text_with_fallback(api_key, prompt, preferred_model="gemini-2.0-flash"):
    """
    推奨モデルでコンテンツを生成する。
    429 (レート制限) 発生時は1分間のクォータリセットを待って自動リトライする。
    """
    client = genai.Client(api_key=api_key)
    
    models_to_try = [preferred_model] if preferred_model else []
    for m in PREFERRED_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

    errors = []
    for model_name in models_to_try:
        for attempt in range(2):
            try:
                print(f"Trying model: {model_name} (attempt {attempt + 1})...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if response and response.text:
                    print(f"Successfully generated content using {model_name}")
                    return response.text, model_name
            except Exception as e:
                err_str = str(e)
                print(f"Model {model_name} attempt {attempt + 1} failed: {err_str}")
                
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    wait_sec = 60
                    print(f"Rate limited (429). Waiting {wait_sec}s for 1-min quota reset...")
                    time.sleep(wait_sec)
                else:
                    errors.append(f"{model_name}: {err_str}")
                    break
        else:
            errors.append(f"{model_name}: Exceeded rate limit after retries.")

    raise RuntimeError(f"すべての代替モデルでの生成に失敗しました。\n詳細:\n" + "\n".join(errors))
