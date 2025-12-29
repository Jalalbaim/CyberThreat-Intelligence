import time
import chromadb

def get_hybrid_context(query, window_minutes=60):
    client = chromadb.PersistentClient(path="./data/chroma_db")
    collection = client.get_collection(name="threat_intel")

    current_time = time.time()
    time_threshold = current_time - (window_minutes * 60)

    # Recherche sémantique (SANS filtre temps)
    results = collection.query(
        query_texts=[query],
        n_results=15
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    if not documents:
        return "No indexed threat intelligence available."

    #Filtrage temporel côté Python (FIABLE)
    filtered_docs = []
    for doc, meta in zip(documents, metadatas):
        ts = meta.get("timestamp", 0)
        if ts >= time_threshold:
            filtered_docs.append(doc)

    # Fallback intelligent
    if not filtered_docs:
        filtered_docs = documents[:5]

    context = "\n---\n".join(filtered_docs)
    return context
