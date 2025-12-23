import pymongo
from datetime import datetime
from graph.models import Node, Edge, Graph
from config.settings import MONGODB_URI, DATABASE_NAME

class GraphBuilder:
    def __init__(self):
        self.client = pymongo.MongoClient(MONGODB_URI)
        self.db = self.client[DATABASE_NAME]
        self.graphs = self.db['graphs']
        self.nodes = self.db['nodes']
        self.edges = self.db['edges']
    
    def build_graph(self, knowledge: dict, source_url: str) -> Graph:
        """Construit un graphe depuis les données LLM"""
        nodes = [Node(**ent) for ent in knowledge.get('entities', [])]
        edges = [Edge(**rel) for rel in knowledge.get('relations', [])]
        
        return Graph(
            nodes=nodes,
            edges=edges,
            source_url=source_url,
            created_at=datetime.now()
        )
    
    def save_graph(self, graph: Graph):
        """Sauvegarde dans MongoDB"""
        graph_doc = {
            'source_url': graph.source_url,
            'created_at': graph.created_at,
            'nodes': [{'name': n.name, 'type': n.type} for n in graph.nodes],
            'edges': [{'source': e.source, 'target': e.target, 'relation': e.relation} 
                      for e in graph.edges]
        }
        self.graphs.insert_one(graph_doc)
    
    def get_all_graphs(self):
        """Récupère tous les graphes"""
        return list(self.graphs.find())