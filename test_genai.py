import os
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("No GEMINI_API_KEY in environment")
else:
    client = genai.Client(api_key=api_key)
    try:
        print("Listing models from Client...")
        for m in client.models.list():
            if 'generateContent' in getattr(m, 'supported_generation_methods', []):
                print("Model:", m.name)
    except Exception as e:
        print("Error listing models:", e)
