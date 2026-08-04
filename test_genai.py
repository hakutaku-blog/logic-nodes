import os
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

models = ["models/gemini-2.5-flash", "models/gemini-2.0-flash-lite", "models/gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.0-flash-lite", "gemini-2.0-flash"]

for m in models:
    try:
        res = client.models.generate_content(model=m, contents="Say hello")
        print(f"SUCCESS for model {m}:", res.text[:30])
        break
    except Exception as e:
        print(f"FAILED for model {m}:", e)
