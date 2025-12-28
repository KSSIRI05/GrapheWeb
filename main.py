from crawler.web_crawler import WebCrawler
from preprocessing.cleaner import clean_text, truncate_text
from llm.extractor import extract_knowledge
from graph.builder import GraphBuilder
from visualization.plotter import visualize_graph

def pipeline(url: str, max_pages: int = 5):
    """Pipeline complet : Crawl → LLM (Groq) → Graph → Viz"""
    print("\n" + "="*60)
    print("🚀 GRAPHCRAWLER - Pipeline avec Groq")
    print("="*60)
    print(f"\n🔍 URL cible: {url}")
    print(f"📄 Pages max: {max_pages}\n")
    
    # Initialiser le builder UNE SEULE FOIS
    builder = GraphBuilder()
    
    # 1. Crawl
    print("⏳ Étape 1/4 : Crawling en cours...")
    crawler = WebCrawler()
    
    try:
        data = crawler.crawl_url(url, content_types=['html'], max_hits=max_pages)
    except Exception as e:
        print(f"❌ Erreur crawl: {e}")
        crawler.close()
        builder.close()
        return
    
    if not data:
        print("❌ Aucune donnée crawlée")
        crawler.close()
        builder.close()
        return
    
    print(f"✅ {len(data)} pages crawlées avec succès\n")
    
    # 2. Traiter chaque page
    print("⏳ Étape 2/4 : Extraction avec Groq...")
    total_entities = 0
    total_relations = 0
    all_graphs = []  # ← Stocker les graphes en mémoire aussi
    
    for i, item in enumerate(data, 1):
        print(f"\n📄 [{i}/{len(data)}] {item['title'][:50]}...")
        
        # Nettoyer
        text = clean_text(item['content'])
        text = truncate_text(text, max_chars=6000)
        
        if len(text) < 100:
            print("   ⚠️  Texte trop court, ignoré")
            continue
        
        # LLM
        print("   🤖 Analyse par Groq...")
        knowledge = extract_knowledge(text)
        
        entities_count = len(knowledge.get('entities', []))
        relations_count = len(knowledge.get('relations', []))
        
        total_entities += entities_count
        total_relations += relations_count
        
        # Graph
        if entities_count > 0:
            graph = builder.build_graph(knowledge, item['url'])
            print(f"   📊 Graphe généré : {len(graph.nodes)} nœuds, {len(graph.edges)} liens")
            
            graph_id = builder.save_graph(graph)
            if graph_id:
                print(f"   💾 Graphe sauvegardé (ID: {graph_id[:8]}...)")
                all_graphs.append(graph)  # ← Garder en mémoire
            else:
                print("   ⚠️  Échec sauvegarde")
        else:
            print("   ⚠️  Aucune entité extraite")
    
    print(f"\n✅ Extraction terminée:")
    print(f"   📊 Total entités: {total_entities}")
    print(f"   🔗 Total relations: {total_relations}\n")
    
    # 3. Récupérer les graphes
    print("⏳ Étape 3/4 : Construction du graphe global...")
    
    if not all_graphs:
        print("❌ Aucun graphe à visualiser")
        crawler.close()
        builder.close()
        return
    
    print(f"✅ {len(all_graphs)} graphe(s) construit(s)\n")
    
    # 4. Visualiser le dernier graphe OU fusionner tous les graphes
    print("⏳ Étape 4/4 : Génération de la visualisation...")
    
    try:
        # Option 1: Visualiser le dernier graphe
        last_graph = all_graphs[-1]
        
        # Convertir en format dict pour le plotter
        graph_dict = {
            'nodes': [{'name': n.name, 'type': n.type} for n in last_graph.nodes],
            'edges': [{'source': e.source, 'target': e.target, 'type': e.type} for e in last_graph.edges],
            'source_url': last_graph.source_url
        }
        
        visualize_graph(graph_dict, "output_graph.png")
        
        # Option 2: Fusionner tous les graphes (décommentez si vous voulez)
        # from graph.models import Graph
        # merged = Graph(nodes=[], edges=[], source_url="Merged", created_at=datetime.now())
        # for g in all_graphs:
        #     merged.merge(g)
        # 
        # merged_dict = {
        #     'nodes': [{'name': n.name, 'type': n.type} for n in merged.nodes],
        #     'edges': [{'source': e.source, 'target': e.target, 'type': e.type} for e in merged.edges],
        #     'source_url': "Graphe fusionné"
        # }
        # visualize_graph(merged_dict, "merged_graph.png")
        
    except Exception as e:
        print(f"❌ Erreur visualisation: {e}")
        import traceback
        traceback.print_exc()
    
    # Nettoyage
    crawler.close()
    builder.close()
    
    print("\n" + "="*60)
    print("🎉 Pipeline terminé avec succès!")
    print("="*60)
    print(f"\n📊 Résumé:")
    print(f"   • Pages analysées: {len(data)}")
    print(f"   • Entités totales: {total_entities}")
    print(f"   • Relations totales: {total_relations}")
    print(f"   • Graphes créés: {len(all_graphs)}")
    print(f"   • Fichier de sortie: output_graph.png\n")

if __name__ == "__main__":
    print("\n🕷️  GRAPHCRAWLER - Powered by Groq\n")
    
    url = input("🌐 Entrez l'URL à crawler: ").strip()
    
    if not url:
        print("❌ URL invalide")
        exit(1)
    
    # Valider l'URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Demander le nombre de pages
    try:
        max_pages = input("📄 Nombre de pages max [5]: ").strip()
        max_pages = int(max_pages) if max_pages else 5
    except:
        max_pages = 5
    
    # Lancer le pipeline
    pipeline(url, max_pages)