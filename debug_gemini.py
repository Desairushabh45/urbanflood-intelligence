import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent / "backend"
load_dotenv(BASE_DIR / ".env")

print(f"[DEBUG] Current dir: {BASE_DIR}")
print(f"[DEBUG] .env file exists: {(BASE_DIR / '.env').exists()}")

api_key = os.getenv("GEMINI_API_KEY")
print(f"[DEBUG] API Key loaded: {bool(api_key)}")
if api_key:
    print(f"[DEBUG] API Key starts with: {api_key[:20]}...")

try:
    from google import genai
    print("[OK] google.genai imported")
    
    client = genai.Client(api_key=api_key)
    print("[OK] Gemini client created")
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Say 'Hello, API working!'"
    )
    print(f"[OK] API Response: {response.text}")
    
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {str(e)}")
