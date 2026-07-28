import json
import urllib.request
from google import genai

def get_available_models(api_key):
    """GoogleのREST APIから利用可能なモデル一覧を動的に取得する"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    req = urllib.request.Request(url)
    
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        
    # 'models/' プレフィックスを外して純粋なモデル名だけを抽出
    available_models = [model.get("name").split("/")[-1] for model in data.get("models", []) if "name" in model]
    return available_models

def generate_text_with_fallback(api_key, prompt, preferred_model="gemini-3.6-flash"):
    """
    指定モデルでの生成を試み、失敗した場合は利用可能なモデルを動的に探して代替実行する
    """
    client = genai.Client(api_key=api_key)
    
    try:
        print(f"Generating content using preferred model: {preferred_model}...")
        response = client.models.generate_content(
            model=preferred_model,
            contents=prompt,
        )
        return response.text, preferred_model
        
    except Exception as e:
        print(f"Preferred model ({preferred_model}) failed: {e}")
        print("Fetching available models for fallback...")
        
        # フォールバック処理：利用可能なモデル一覧を取得
        models = get_available_models(api_key)
        
        # テキスト生成に適したモデル（flashを含み、特化型でないもの）を抽出
        text_models = [m for m in models if "flash" in m and "tts" not in m and "image" not in m and "embedding" not in m]
        
        if not text_models:
            raise Exception("フォールバック用の利用可能なテキスト生成モデルが見つかりませんでした。")
            
        # リストの先頭（利用可能な最新・推奨モデル）を代替として選択
        fallback_model = text_models[0]
        print(f"Fallback model selected: {fallback_model}. Retrying...")
        
        response = client.models.generate_content(
            model=fallback_model,
            contents=prompt,
        )
        return response.text, fallback_model
