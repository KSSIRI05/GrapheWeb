import re

def clean_text(text: str) -> str:
    """Nettoie le texte crawlé"""
    # Supprimer espaces multiples
    text = re.sub(r'\s+', ' ', text)
    # Supprimer caractères spéciaux
    text = re.sub(r'[^\w\s\.,;:!?\-]', '', text)
    return text.strip()

def truncate_text(text: str, max_chars: int = 10000) -> str:
    """Limite la taille pour le LLM"""
    return text[:max_chars]