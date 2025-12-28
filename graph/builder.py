import pymongo
from datetime import datetime
from graph.models import Node, Edge, Graph
from config.settings import MONGODB_URI, DATABASE_NAME
import logging

# Configurer le logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GraphBuilder:
    def __init__(self):
        try:
            self.client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
            
            self.db = self.client[DATABASE_NAME]
            self.graphs = self.db['graphs']
            self.nodes = self.db['nodes']
            self.edges = self.db['edges']
            
            try:
                self.graphs.create_index('source_url')
                self.graphs.create_index('created_at')
            except:
                pass
                
            logger.info("✅ GraphBuilder initialisé")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation GraphBuilder: {e}")
            print(f"\n⚠️  ERREUR MONGODB: {e}")
            raise
    
    def build_graph(self, knowledge: dict, source_url: str) -> Graph:
        """Construit un graphe depuis les données LLM"""
        if not knowledge:
            return Graph(nodes=[], edges=[], source_url=source_url, created_at=datetime.now())
        
        # ===== CONSTRUIRE LES NŒUDS =====
        nodes = []
        entities = knowledge.get('entities', [])
        
        if not isinstance(entities, list):
            entities = []
        
        for ent in entities:
            try:
                if not isinstance(ent, dict):
                    continue
                
                # Extraire le nom et le type
                name = ent.get('name', '')
                ent_type = ent.get('type', 'Unknown')
                
                # Convertir en string et nettoyer
                if not name:
                    continue
                
                name = str(name).strip()
                ent_type = str(ent_type).strip()
                
                if not name:  # Vérifier après strip
                    continue
                
                node_data = {
                    'name': name,
                    'type': ent_type,
                    'metadata': ent.get('metadata', None)
                }
                
                nodes.append(Node(**node_data))
                
            except Exception as e:
                logger.warning(f"Erreur création nœud: {e} - Entité: {ent}")
                continue
        
        # ===== CONSTRUIRE LES ARÊTES =====
        edges = []
        relations = knowledge.get('relations', [])
        
        if not isinstance(relations, list):
            relations = []
        
        # Créer un dictionnaire pour normaliser les noms (insensible à la casse)
        node_names = {n.name: n.name for n in nodes}
        node_names_lower = {n.name.lower(): n.name for n in nodes}
        
        for rel in relations:
            try:
                if not isinstance(rel, dict):
                    continue
                
                source = str(rel.get('source', '')).strip()
                target = str(rel.get('target', '')).strip()
                rel_type = str(rel.get('type', 'related_to')).strip()
                
                if not source or not target:
                    continue
                
                # Essayer de trouver les nœuds (insensible à la casse)
                source_normalized = node_names_lower.get(source.lower(), source)
                target_normalized = node_names_lower.get(target.lower(), target)
                
                # Si les nœuds n'existent pas, les créer
                if source_normalized not in node_names:
                    new_node = Node(name=source, type='Unknown', metadata=None)
                    nodes.append(new_node)
                    node_names[source] = source
                    node_names_lower[source.lower()] = source
                    source_normalized = source
                
                if target_normalized not in node_names:
                    new_node = Node(name=target, type='Unknown', metadata=None)
                    nodes.append(new_node)
                    node_names[target] = target
                    node_names_lower[target.lower()] = target
                    target_normalized = target
                
                edge_data = {
                    'source': source_normalized,
                    'target': target_normalized,
                    'type': rel_type,
                    'weight': float(rel.get('weight', 1.0))
                }
                
                edges.append(Edge(**edge_data))
                
            except Exception as e:
                logger.warning(f"Erreur création arête: {e} - Relation: {rel}")
                continue
        
        print(f"   📊 Graphe généré : {len(nodes)} nœuds, {len(edges)} liens")
        logger.info(f"Graphe créé: {len(nodes)} nœuds, {len(edges)} arêtes")
        
        return Graph(
            nodes=nodes,
            edges=edges,
            source_url=source_url,
            created_at=datetime.now()
        )
    
    def save_graph(self, graph: Graph):
        """Sauvegarde dans MongoDB"""
        try:
            if not graph.nodes:
                return None
            
            graph_doc = {
                'source_url': graph.source_url,
                'created_at': graph.created_at,
                'nodes': [
                    {'name': str(n.name), 'type': str(n.type), 'metadata': n.metadata} 
                    for n in graph.nodes
                ],
                'edges': [
                    {'source': str(e.source), 'target': str(e.target), 'type': str(e.type), 'weight': float(e.weight)} 
                    for e in graph.edges
                ],
                'stats': {
                    'num_nodes': len(graph.nodes),
                    'num_edges': len(graph.edges),
                }
            }
            
            result = self.graphs.insert_one(graph_doc)
            graph_id = str(result.inserted_id)
            logger.info(f"Graphe sauvegardé: {graph_id}")
            return graph_id
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde: {e}")
            print(f"   ❌ Erreur sauvegarde: {e}")
            return None
    
    def get_all_graphs(self):
        """Récupère tous les graphes"""
        try:
            return list(self.graphs.find().sort('created_at', -1))
        except Exception as e:
            logger.error(f"Erreur récupération: {e}")
            return []
    
    def close(self):
        """Ferme la connexion MongoDB"""
        try:
            self.client.close()
            logger.info("Connexion MongoDB fermée")
        except Exception as e:
            logger.error(f"Erreur fermeture: {e}")