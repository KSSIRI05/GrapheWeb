import json
import re
from llm.client import call_groq

EXTRACTION_SYSTEM = """Tu es un expert en extraction d'informations structurées depuis du texte.

Ta tâche est d'analyser le texte fourni et d'extraire :
1. Les ENTITÉS : personnes, lieux, organisations, concepts, dates, technologies
2. Les RELATIONS : liens sémantiques entre les entités

RÈGLES STRICTES :
- Retourne UNIQUEMENT un JSON valide
- Pas de texte avant ou après le JSON
- Pas de markdown (pas de ```json)
- Format exact comme ci-dessous"""

EXTRACTION_PROMPT = """
Analyse ce texte et extrait les entités et relations.

Format JSON attendu :
{{
  "entities": [
    {{"name": "Nom exact", "type": "Person|Location|Organization|Concept|Date|Technology"}}
  ],
  "relations": [
    {{"source": "Entité source", "target": "Entité cible", "type": "type_relation"}}
  ]
}}

TEXTE À ANALYSER :
---
{text}
---

Retourne UNIQUEMENT le JSON sans autre texte :
"""

def extract_knowledge(text: str) -> dict:
    """Extrait entités et relations avec Groq"""
    
    # Limiter la taille du texte
    text = text[:6000]  # Groq/Llama gère bien jusqu'à 6000 chars
    
    # Préparer le prompt
    prompt = EXTRACTION_PROMPT.format(text=text)
    
    # Appeler Groq
    response = call_groq(prompt, system=EXTRACTION_SYSTEM)
    
    if not response:
        print("   ⚠️  Pas de réponse de Groq")
        return {"entities": [], "relations": []}
    
    try:
        # Nettoyer la réponse
        response = response.strip()
        
        # Supprimer les balises markdown si présentes
        if "```json" in response:
            response = re.sub(r'```json\s*', '', response)
        if "```" in response:
            response = re.sub(r'```\s*', '', response)
        
        # Extraire le JSON s'il y a du texte autour
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            response = json_match.group(0)
        
        # Parser le JSON
        data = json.loads(response)
        
        # Valider la structure
        if not isinstance(data, dict):
            raise ValueError("La réponse n'est pas un dictionnaire")
        
        entities = data.get('entities', [])
        relations = data.get('relations', [])
        
        # Valider les entités
        if not isinstance(entities, list):
            entities = []
        
        # Valider les relations
        if not isinstance(relations, list):
            relations = []
        
        print(f"   ✅ Extraction réussie: {len(entities)} entités, {len(relations)} relations")
        
        return {
            "entities": entities,
            "relations": relations
        }
        
    except json.JSONDecodeError as e:
        print(f"   ❌ Erreur JSON: {e}")
        print(f"   Réponse brute (200 premiers chars): {response[:200]}...")
        return {"entities": [], "relations": []}
    
    except Exception as e:
        print(f"   ❌ Erreur extraction: {e}")
        return {"entities": [], "relations": []}