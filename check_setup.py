# check_setup.py
import sys

print("🔍 Vérification de l'installation\n")
print("="*50)

# 1. Vérifier MongoDB
print("\n1️⃣ Test MongoDB...")
try:
    import pymongo
    client = pymongo.MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("   ✅ MongoDB connecté")
    client.close()
except Exception as e:
    print(f"   ❌ MongoDB non accessible: {e}")
    print("   💡 Lancez: mongod --dbpath C:\\data\\db")
    sys.exit(1)

# 2. Vérifier Groq
print("\n2️⃣ Test Groq API...")
try:
    from llm.client import call_groq
    response = call_groq("Dis juste OK")
    if response:
        print("   ✅ Groq API fonctionne")
    else:
        print("   ❌ Groq ne répond pas")
except Exception as e:
    print(f"   ❌ Erreur Groq: {e}")

# 3. Vérifier GraphBuilder
print("\n3️⃣ Test GraphBuilder...")
try:
    from graph.builder import GraphBuilder
    builder = GraphBuilder()
    
    # Vérifier la méthode close
    if hasattr(builder, 'close'):
        print("   ✅ Méthode close() présente")
        builder.close()
    else:
        print("   ❌ Méthode close() manquante")
        print("   💡 Ajoutez-la dans graph/builder.py")
except Exception as e:
    print(f"   ❌ Erreur GraphBuilder: {e}")

# 4. Vérifier les autres modules
print("\n4️⃣ Test des autres modules...")
modules = [
    ('crawler.web_crawler', 'WebCrawler'),
    ('preprocessing.cleaner', 'clean_text'),
    ('llm.extractor', 'extract_knowledge'),
    ('visualization.plotter', 'visualize_graph'),
]

all_ok = True
for module_name, item_name in modules:
    try:
        module = __import__(module_name, fromlist=[item_name])
        getattr(module, item_name)
        print(f"   ✅ {module_name}")
    except Exception as e:
        print(f"   ❌ {module_name}: {e}")
        all_ok = False

print("\n" + "="*50)
if all_ok:
    print("🎉 Tout est prêt ! Lancez: python main.py")
else:
    print("⚠️  Certains composants ont des problèmes")