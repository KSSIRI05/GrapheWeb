import json
from llm.client import call_gemini

EXTRACTION_PROMPT = """
Tu es un expert en extraction d'informations structurées.

Analyse ce texte et extrait :
1. **Entités** : personnes, lieux, organisations, concepts, dates
2. **Relations** : liens entre les entités

**IMPORTANT** : Retourne UNIQUEMENT un JSON valide, sans texte avant ou après.

Format attendu :
{
  "entities": [
    {"name": "Nom de l'entité", "type": "Person|Location|Organization|Concept|Date"}
  ],
  "relations": [
    {"source": "Entité 1", "target": "Entité 2", "type": "type_de_relation"}
  ]
}

TEXTE À ANALYSER:
{text}

JSON :
"""

def extract_knowledge(text: str) -> dict:
    """Extrait entités et relations avec Gemini"""
    prompt = EXTRACTION_PROMPT.format(text=text[:5000])  # Limite pour éviter dépassement
    response = call_gemini(prompt)
    
    try:
        # Nettoyer la réponse
        response = response.strip()
        
        # Gemini peut entourer le JSON de ```json
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        
        response = response.strip()
        
        # Parser le JSON
        data = json.loads(response)
        
        print(f"   ✅ Extraction réussie: {len(data.get('entities', []))} entités, {len(data.get('relations', []))} relations")
        return data
        
    except json.JSONDecodeError as e:
        print(f"   ❌ Erreur JSON: {e}")
        print(f"   Réponse brute: {response[:200]}...")
        return {"entities": [], "relations": []}
    except Exception as e:
        print(f"   ❌ Erreur extraction: {e}")
        return {"entities": [], "relations": []}