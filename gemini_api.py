import os
import time
from google import genai

# 確実に動作する推奨モデルのフォールバック優先順位リスト
PREFERRED_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-2.0-flash-lite",
]

def generate_text_with_fallback(api_key, prompt, preferred_model="gemini-2.5-flash"):
    """
    指定モデルおよびフォールバックモデルを試行する。
    429 (レート制限/過負荷) 発生時は15秒待機して自動リトライを行う。
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
                
                # 429 レート制限の場合は待機して再試行
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    wait_sec = 15 * (attempt + 1)
                    print(f"Rate limited (429). Waiting {wait_sec}s before retrying...")
                    time.sleep(wait_sec)
                else:
                    errors.append(f"{model_name}: {err_str}")
                    break
        else:
            errors.append(f"{model_name}: Rate limit exceeded after retries.")

    raise RuntimeError(f"すべての代替モデルでの生成に失敗しました。\nエラー詳細:\n" + "\n".join(errors))
