
import requests
from bs4 import BeautifulSoup
import pymongo
from datetime import datetime
import schedule
import time
import pdfplumber
import io
from typing import List, Dict
import threading
import logging
from urllib.parse import urljoin, urlparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebCrawler:
    """Classe principale pour le crawler web"""
    
    def __init__(self, mongo_uri="mongodb://localhost:27017/", 
                 db_name="web_crawler_db"):
        """Initialise le crawler avec MongoDB"""
        try:
            self.client = pymongo.MongoClient(mongo_uri)
            self.db = self.client[db_name]
            self.sources_collection = self.db['sources']
            self.data_collection = self.db['crawled_data']
            
            # Créer des index
            self.data_collection.create_index([('title', 'text'), ('content', 'text')])
            self.data_collection.create_index('source_id')
            self.data_collection.create_index('timestamp')
            
            logger.info(f"Connexion MongoDB établie: {db_name}")
        except Exception as e:
            logger.error(f"Erreur de connexion MongoDB: {e}")
            raise
    
    def add_source(self, url, source_type='website',
                   frequency='daily', schedule_time='09:00',
                   max_hits=100, content_types=None,
                   enabled=True):
        """Ajoute une nouvelle source à crawler"""
        if content_types is None:
            content_types = ['html', 'text']
        
        source = {
            'url': url,
            'type': source_type,
            'frequency': frequency,
            'schedule_time': schedule_time,
            'max_hits': max_hits,
            'content_types': content_types,
            'enabled': enabled,
            'last_crawl': None,
            'status': 'pending',
            'created_at': datetime.now()
        }
        
        result = self.sources_collection.insert_one(source)
        logger.info(f"Source ajoutée: {url}")
        return str(result.inserted_id)
    
    def get_sources(self, enabled_only=False):
        """Récupère toutes les sources"""
        query = {'enabled': True} if enabled_only else {}
        sources = list(self.sources_collection.find(query))
        for source in sources:
            source['_id'] = str(source['_id'])
        return sources
    
    def delete_source(self, source_id):
        """Supprime une source et ses données"""
        try:
            from bson.objectid import ObjectId
            self.data_collection.delete_many({'source_id': source_id})
            result = self.sources_collection.delete_one({'_id': ObjectId(source_id)})
            logger.info(f"Source supprimée: {source_id}")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Erreur suppression: {e}")
            return False
    
    def crawl_url(self, url, content_types, max_hits=100):
        """Crawl une URL et collecte les données"""
        collected_data = []
        visited_urls = set()
        urls_to_visit = [url]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        # Configuration de la session avec retry
        import requests
        from requests.adapters import HTTPAdapter
        from requests.packages.urllib3.util.retry import Retry
        
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        while urls_to_visit and len(collected_data) < max_hits:
            current_url = urls_to_visit.pop(0)
            
            if current_url in visited_urls:
                continue
            
            visited_urls.add(current_url)
            
            try:
                logger.info(f"Tentative de crawl: {current_url}")
                
                response = session.get(
                    current_url, 
                    headers=headers, 
                    timeout=30,  # ← Timeout augmenté
                    allow_redirects=True
                )
                response.raise_for_status()
                
                content_type = response.headers.get('Content-Type', '').lower()
                
                if 'html' in content_type and 'html' in content_types:
                    data = self._process_html(current_url, response.content)
                    if data:
                        collected_data.append(data)
                        if len(collected_data) < max_hits:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            for link in soup.find_all('a', href=True):
                                absolute_url = urljoin(current_url, link['href'])
                                if self._is_same_domain(url, absolute_url):
                                    urls_to_visit.append(absolute_url)
                
                elif 'xml' in content_type and 'xml' in content_types:
                    data = self._process_xml(current_url, response.content)
                    if data:
                        collected_data.append(data)
                
                elif 'pdf' in content_type and 'pdf' in content_types:
                    data = self._process_pdf(current_url, response.content)
                    if data:
                        collected_data.append(data)
                
                elif 'text' in content_type and 'text' in content_types:
                    data = self._process_text(current_url, response.text)
                    if data:
                        collected_data.append(data)
                
            except Exception as e:
                logger.warning(f"Erreur crawl {current_url}: {e}")
                continue
        
        return collected_data
    
    def _is_same_domain(self, base_url, check_url):
        """Vérifie si deux URLs sont du même domaine"""
        return urlparse(base_url).netloc == urlparse(check_url).netloc
    
    def _process_html(self, url, content):
        """Traite le contenu HTML"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            for script in soup(['script', 'style']):
                script.decompose()
            
            title = soup.title.string if soup.title else 'Sans titre'
            text_content = soup.get_text(separator=' ', strip=True)
            
            keywords = []
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords and meta_keywords.get('content'):
                keywords = [k.strip() for k in meta_keywords['content'].split(',')]
            
            return {
                'url': url,
                'title': title,
                'content': text_content[:5000],
                'content_type': 'html',
                'keywords': keywords,
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Erreur traitement HTML: {e}")
            return None
    
    def _process_xml(self, url, content):
        """Traite le contenu XML/RSS"""
        try:
            soup = BeautifulSoup(content, 'xml')
            items = soup.find_all('item')
            if items:
                item = items[0]
                title = item.find('title').text if item.find('title') else 'Sans titre'
                description = item.find('description').text if item.find('description') else ''
                
                return {
                    'url': url,
                    'title': title,
                    'content': description[:5000],
                    'content_type': 'xml',
                    'keywords': [],
                    'timestamp': datetime.now()
                }
            return None
        except Exception as e:
            logger.error(f"Erreur traitement XML: {e}")
            return None
    
    def _process_pdf(self, url, content):
        """Traite le contenu PDF"""
        try:
            pdf_file = io.BytesIO(content)
            text_content = ""
            
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages[:10]:
                    text_content += page.extract_text() or ""
            
            return {
                'url': url,
                'title': url.split('/')[-1],
                'content': text_content[:5000],
                'content_type': 'pdf',
                'keywords': [],
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Erreur traitement PDF: {e}")
            return None
    
    def _process_text(self, url, content):
        """Traite le contenu texte brut"""
        try:
            return {
                'url': url,
                'title': url.split('/')[-1],
                'content': content[:5000],
                'content_type': 'text',
                'keywords': [],
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Erreur traitement texte: {e}")
            return None
    
    def crawl_source(self, source_id):
        """Crawl une source spécifique"""
        try:
            from bson.objectid import ObjectId
            source = self.sources_collection.find_one({'_id': ObjectId(source_id)})
            
            if not source or not source.get('enabled'):
                logger.warning(f"Source {source_id} non trouvée ou désactivée")
                return 0
            
            logger.info(f"Début crawl: {source['url']}")
            
            self.sources_collection.update_one(
                {'_id': ObjectId(source_id)},
                {'$set': {'status': 'crawling'}}
            )
            
            collected_data = self.crawl_url(
                source['url'],
                source['content_types'],
                source['max_hits']
            )
            
            count = 0
            for data in collected_data:
                data['source_id'] = source_id
                self.data_collection.insert_one(data)
                count += 1
            
            self.sources_collection.update_one(
                {'_id': ObjectId(source_id)},
                {'$set': {
                    'status': 'completed',
                    'last_crawl': datetime.now()
                }}
            )
            
            logger.info(f"Crawl terminé: {count} éléments")
            return count
            
        except Exception as e:
            logger.error(f"Erreur crawl: {e}")
            return 0
    
    def search_data(self, query, limit=50):
        """Recherche par mots-clés"""
        try:
            results = list(self.data_collection.find(
                {'$text': {'$search': query}},
                {'score': {'$meta': 'textScore'}}
            ).sort([('score', {'$meta': 'textScore'})]).limit(limit))
            
            for result in results:
                result['_id'] = str(result['_id'])
            
            logger.info(f"Recherche '{query}': {len(results)} résultats")
            return results
            
        except Exception as e:
            logger.error(f"Erreur recherche: {e}")
            return []
    
    def get_statistics(self):
        """Obtient les statistiques"""
        return {
            'total_sources': self.sources_collection.count_documents({}),
            'active_sources': self.sources_collection.count_documents({'enabled': True}),
            'total_data': self.data_collection.count_documents({}),
            'last_update': datetime.now()
        }
    
    def schedule_crawls(self):
        """Configure le planificateur"""
        sources = self.get_sources(enabled_only=True)
        
        for source in sources:
            source_id = source['_id']
            frequency = source['frequency']
            schedule_time = source.get('schedule_time', '09:00')
            
            if frequency == 'hourly':
                schedule.every().hour.do(self.crawl_source, source_id)
            elif frequency == 'daily':
                schedule.every().day.at(schedule_time).do(self.crawl_source, source_id)
            elif frequency == 'weekly':
                schedule.every().week.at(schedule_time).do(self.crawl_source, source_id)
            elif frequency == 'monthly':
                schedule.every(30).days.at(schedule_time).do(self.crawl_source, source_id)
        
        logger.info(f"Planificateur configuré pour {len(sources)} sources")
        
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("Planificateur démarré")
    
    def close(self):
        """Ferme la connexion MongoDB"""
        self.client.close()
        logger.info("Connexion fermée")


def main():
    """Interface console interactive"""
    print("=" * 60)
    print("SYSTÈME DE WEB CRAWLER CONFIGURABLE")
    print("=" * 60)
    
    crawler = WebCrawler()
    
    while True:
        print("\n--- MENU PRINCIPAL ---")
        print("1. Ajouter une source")
        print("2. Lister les sources")
        print("3. Crawler une source")
        print("4. Crawler toutes les sources actives")
        print("5. Rechercher dans les données")
        print("6. Voir les statistiques")
        print("7. Supprimer une source")
        print("8. Démarrer le planificateur")
        print("9. Quitter")
        
        choice = input("\nVotre choix: ").strip()
        
        if choice == '1':
            print("\n--- AJOUTER UNE SOURCE ---")
            url = input("URL: ").strip()
            source_type = input("Type [website]: ").strip() or 'website'
            frequency = input("Fréquence [daily]: ").strip() or 'daily'
            schedule_time = input("Heure [09:00]: ").strip() or '09:00'
            max_hits = int(input("Max pages [100]: ").strip() or '100')
            content_types_input = input("Types [html,text]: ").strip() or 'html,text'
            content_types = [ct.strip() for ct in content_types_input.split(',')]
            
            source_id = crawler.add_source(
                url=url,
                source_type=source_type,
                frequency=frequency,
                schedule_time=schedule_time,
                max_hits=max_hits,
                content_types=content_types
            )
            print(f"\n✓ Source ajoutée! ID: {source_id}")
        
        elif choice == '2':
            sources = crawler.get_sources()
            print(f"\n--- SOURCES ({len(sources)}) ---")
            for i, source in enumerate(sources, 1):
                print(f"\n{i}. ID: {source['_id']}")
                print(f"   URL: {source['url']}")
                print(f"   Type: {source['type']}")
                print(f"   Fréquence: {source['frequency']}")
                print(f"   Actif: {'Oui' if source['enabled'] else 'Non'}")
                print(f"   Dernier crawl: {source.get('last_crawl', 'Jamais')}")
        
        elif choice == '3':
            source_id = input("\nID de la source: ").strip()
            count = crawler.crawl_source(source_id)
            print(f"\n✓ {count} éléments collectés")
        
        elif choice == '4':
            sources = crawler.get_sources(enabled_only=True)
            print(f"\nCrawl de {len(sources)} sources...")
            total = 0
            for source in sources:
                count = crawler.crawl_source(source['_id'])
                total += count
            print(f"\n✓ Total: {total} éléments")
        
        elif choice == '5':
            query = input("\nRecherche: ").strip()
            results = crawler.search_data(query)
            print(f"\n--- RÉSULTATS ({len(results)}) ---")
            for i, result in enumerate(results[:10], 1):
                print(f"\n{i}. {result['title']}")
                print(f"   URL: {result['url']}")
                print(f"   Type: {result['content_type']}")
                print(f"   Extrait: {result['content'][:150]}...")
        
        elif choice == '6':
            stats = crawler.get_statistics()
            print("\n--- STATISTIQUES ---")
            print(f"Total sources: {stats['total_sources']}")
            print(f"Sources actives: {stats['active_sources']}")
            print(f"Total données: {stats['total_data']}")
        
        elif choice == '7':
            source_id = input("\nID à supprimer: ").strip()
            if crawler.delete_source(source_id):
                print("\n✓ Source supprimée")
            else:
                print("\n✗ Erreur")
        
        elif choice == '8':
            print("\nDémarrage du planificateur...")
            crawler.schedule_crawls()
            print("✓ Actif (Ctrl+C pour arrêter)")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\nArrêté")
        
        elif choice == '9':
            crawler.close()
            print("\nAu revoir!")
            break


if __name__ == "__main__":
    main()
