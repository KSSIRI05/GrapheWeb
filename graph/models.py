from dataclasses import dataclass
from typing import List
from datetime import datetime

@dataclass
class Node:
    name: str
    type: str
    metadata: dict = None

@dataclass
class Edge:
    source: str
    target: str
    relation: str
    weight: float = 1.0

@dataclass
class Graph:
    nodes: List[Node]
    edges: List[Edge]
    source_url: str
    created_at: datetime