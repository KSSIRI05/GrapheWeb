import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# CRITICAL FIX: Explicitly set the client to use 'v1'
# This stops the SDK from looking in the 'v1beta' folder where the 404 occurs
client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(api_version='v1')
)

try:
    # TRY THIS FIRST: The standard stable name
    # If this still 404s, change to "gemini-1.5-flash-latest"
    response = client.models.generate_content(
        model="gemini-1.5-flash", 
        contents="Dis juste 'Gemini fonctionne!'"
    )
    print(f"✅ Success! Response: {response.text}")

except Exception as e:
    print(f"❌ Still failing. Error details: {e}")
    
    # DEBUG STEP: If it still fails, let's see exactly what models YOU have access to
    print("\n🔍 Checking your available models...")
    for m in client.models.list():
        print(f" - {m.name}")