from openai import OpenAI
from dotenv import load_dotenv
import os

print("🔍 Test de Groq...\n")

# Charger .env
load_dotenv()

# Récupérer les variables
api_key = os.getenv("GROQ_API_KEY")
base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
model = os.getenv("MODEL", "llama-3.3-70b-versatile")

print(f"🔑 API Key: {api_key[:15]}..." if api_key else "❌ GROQ_API_KEY manquante")
print(f"🌐 Base URL: {base_url}")
print(f"🤖 Modèle: {model}\n")

if not api_key:
    print("❌ Ajoutez GROQ_API_KEY dans votre fichier .env")
    exit(1)

# Test de connexion
try:
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    print("📤 Envoi d'un test à Groq...")
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Tu es un assistant concis."},
            {"role": "user", "content": "Dis juste 'Groq fonctionne parfaitement!'"}
        ],
        max_tokens=50,
        temperature=0.1
    )
    
    result = response.choices[0].message.content
    print(f"✅ Réponse Groq: {result}\n")
    
    # Test d'extraction
    print("📊 Test d'extraction de connaissances...")
    
    test_text = "Elon Musk est le PDG de Tesla et SpaceX. Tesla fabrique des voitures électriques."
    
    extraction_response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Tu es un expert en extraction d'entités. Retourne UNIQUEMENT un JSON."
            },
            {
                "role": "user",
                "content": f"""Extrait les entités et relations de ce texte :

{test_text}

Format JSON :
{{
  "entities": [{{"name": "...", "type": "..."}}],
  "relations": [{{"source": "...", "target": "...", "type": "..."}}]
}}"""
            }
        ],
        max_tokens=500,
        temperature=0.1
    )
    
    extraction_result = extraction_response.choices[0].message.content
    print(f"📝 Extraction:\n{extraction_result}\n")
    
    print("🎉 Tous les tests réussis!")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    print("\n💡 Vérifiez :")
    print("  1. Votre clé API Groq est valide (gsk_...)")
    print("  2. Le base_url est https://api.groq.com/openai/v1")
    print("  3. Le modèle existe (essayez llama-3.3-70b-versatile)")
    exit(1)