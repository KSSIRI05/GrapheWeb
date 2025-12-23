import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load variables (ensure GEMINI_API_KEY is in your .env)
load_dotenv()

# Configuration from your settings
from config.settings import GEMINI_API_KEY, MODEL, MAX_TOKENS

if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY manquante!")

# 1. Initialize modern Client
# Forcing api_version='v1' resolves the "Model not found" 404 error
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(api_version='v1')
)

print(f"✅ Gemini {MODEL} initialisé via google-genai")

def call_gemini(prompt: str, system: str = "") -> str:
    """Appelle Gemini API avec le nouveau SDK unified"""
    try:
        # 2. Configuration mapping
        # In the new SDK, system_instruction is part of GenerateContentConfig
        config = types.GenerateContentConfig(
            system_instruction=system if system else None,
            temperature=0.1,
            max_output_tokens=MAX_TOKENS,
        )
        
        # 3. Execution
        # Use client.models.generate_content instead of a standalone model object
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=config
        )
        
        return response.text
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Erreur appel Gemini: {error_msg}")
        
        # 4. Error handling
        if "429" in error_msg:
            print("→ Quota dépassé (RESOURCE_EXHAUSTED). Attendez 60s ou vérifiez votre forfait.")
        elif "404" in error_msg:
            print("→ Modèle introuvable. Vérifiez que MODEL est bien 'gemini-1.5-flash'.")
        elif "401" in error_msg:
            print("→ Clé API invalide.")
            
        return ""

# Alias for compatibility
call_claude = call_gemini