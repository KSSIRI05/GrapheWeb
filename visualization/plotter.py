import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

def visualize_graph(graph_data: Dict, output_file: str = "output_graph.png"):
    """
    Visualise un graphe de connaissances avec NetworkX
    
    Args:
        graph_data: Dictionnaire contenant 'nodes' et 'edges'
        output_file: Chemin du fichier de sortie
    """
    try:
        # Créer un graphe dirigé
        G = nx.DiGraph()
        
        # Extraire les nœuds et arêtes
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])
        
        if not nodes:
            print("⚠️  Aucun nœud à visualiser")
            return
        
        print(f"📊 Création du graphe: {len(nodes)} nœuds, {len(edges)} arêtes")
        
        # Ajouter les nœuds avec leurs types
        node_colors = []
        node_types = {}
        
        for node in nodes:
            node_name = node.get('name', 'Unknown')
            node_type = node.get('type', 'Unknown')
            
            G.add_node(node_name, type=node_type)
            node_types[node_name] = node_type
            
            # Couleurs selon le type
            color_map = {
                'Person': '#FF6B6B',
                'Location': '#4ECDC4',
                'Organization': '#45B7D1',
                'Concept': '#FFA07A',
                'Date': '#98D8C8',
                'Technology': '#6C5CE7',
                'Product': '#FDCB6E',
                'Personne': '#FF6B6B',
                'Entreprise': '#45B7D1',
                'Produit': '#FDCB6E',
            }
            node_colors.append(color_map.get(node_type, '#95A5A6'))
        
        # Ajouter les arêtes avec leurs relations
        edge_labels = {}
        for edge in edges:
            source = edge.get('source', '')
            target = edge.get('target', '')
            relation = edge.get('type', 'related_to')
            
            # Vérifier que source et target existent
            if source in G.nodes() and target in G.nodes():
                G.add_edge(source, target, relation=relation)
                edge_labels[(source, target)] = relation
        
        # Configuration de la figure
        plt.figure(figsize=(16, 10))
        plt.clf()
        
        # Layout pour positionner les nœuds
        if len(G.nodes()) > 0:
            # Utiliser spring_layout pour un rendu agréable
            pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
            
            # Dessiner les nœuds
            nx.draw_networkx_nodes(
                G, pos,
                node_color=node_colors,
                node_size=3000,
                alpha=0.9,
                edgecolors='white',
                linewidths=2
            )
            
            # Dessiner les arêtes
            nx.draw_networkx_edges(
                G, pos,
                edge_color='#95A5A6',
                arrows=True,
                arrowsize=20,
                arrowstyle='->',
                width=2,
                alpha=0.6,
                connectionstyle='arc3,rad=0.1'
            )
            
            # Labels des nœuds
            nx.draw_networkx_labels(
                G, pos,
                font_size=10,
                font_weight='bold',
                font_color='white'
            )
            
            # Labels des arêtes
            nx.draw_networkx_edge_labels(
                G, pos,
                edge_labels=edge_labels,
                font_size=8,
                font_color='#2C3E50',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7)
            )
            
            # Titre
            source_url = graph_data.get('source_url', 'Unknown')
            plt.title(
                f'Graphe de Connaissances\nSource: {source_url[:60]}...',
                fontsize=14,
                fontweight='bold',
                pad=20
            )
            
            # Légende des types
            unique_types = set(node_types.values())
            legend_elements = []
            color_map = {
                'Person': '#FF6B6B',
                'Location': '#4ECDC4',
                'Organization': '#45B7D1',
                'Concept': '#FFA07A',
                'Date': '#98D8C8',
                'Technology': '#6C5CE7',
                'Product': '#FDCB6E',
                'Personne': '#FF6B6B',
                'Entreprise': '#45B7D1',
                'Produit': '#FDCB6E',
            }
            
            from matplotlib.patches import Patch
            for node_type in unique_types:
                color = color_map.get(node_type, '#95A5A6')
                legend_elements.append(Patch(facecolor=color, label=node_type))
            
            plt.legend(
                handles=legend_elements,
                loc='upper left',
                fontsize=10,
                frameon=True,
                fancybox=True,
                shadow=True
            )
            
            plt.axis('off')
            plt.tight_layout()
            
            # Sauvegarder
            plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"✅ Graphe sauvegardé: {output_file}")
            
            # Afficher les statistiques
            print(f"\n📈 Statistiques du graphe:")
            print(f"   • Nœuds: {G.number_of_nodes()}")
            print(f"   • Arêtes: {G.number_of_edges()}")
            print(f"   • Densité: {nx.density(G):.3f}")
            
            if G.number_of_nodes() > 0:
                # Calculer les centralités
                try:
                    degree_cent = nx.degree_centrality(G)
                    top_nodes = sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:3]
                    print(f"   • Nœuds les plus connectés:")
                    for node, cent in top_nodes:
                        print(f"     - {node}: {cent:.3f}")
                except:
                    pass
        
        else:
            print("⚠️  Graphe vide")
            
    except Exception as e:
        print(f"❌ Erreur lors de la visualisation: {e}")
        import traceback
        traceback.print_exc()


def visualize_multiple_graphs(graphs_data: List[Dict], output_file: str = "combined_graph.png"):
    """
    Combine et visualise plusieurs graphes
    
    Args:
        graphs_data: Liste de dictionnaires de graphes
        output_file: Chemin du fichier de sortie
    """
    try:
        # Créer un graphe combiné
        G = nx.DiGraph()
        all_nodes = []
        all_edges = []
        
        # Fusionner tous les graphes
        for graph_data in graphs_data:
            nodes = graph_data.get('nodes', [])
            edges = graph_data.get('edges', [])
            all_nodes.extend(nodes)
            all_edges.extend(edges)
        
        # Dédupliquer les nœuds
        unique_nodes = {}
        for node in all_nodes:
            name = node.get('name')
            if name not in unique_nodes:
                unique_nodes[name] = node
        
        # Créer le graphe combiné
        combined_graph = {
            'nodes': list(unique_nodes.values()),
            'edges': all_edges,
            'source_url': f"Combined from {len(graphs_data)} sources"
        }
        
        # Visualiser
        visualize_graph(combined_graph, output_file)
        
    except Exception as e:
        print(f"❌ Erreur lors de la visualisation combinée: {e}")