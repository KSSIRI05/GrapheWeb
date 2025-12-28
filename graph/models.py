from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class Node:
    """Représente une entité dans le graphe"""
    name: str
    type: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Edge:
    """Représente une relation entre deux entités"""
    source: str
    target: str
    type: str
    weight: float = 1.0

@dataclass
class Graph:
    """Représente un graphe de connaissances complet"""
    nodes: List[Node]
    edges: List[Edge]
    source_url: str
    created_at: datetime