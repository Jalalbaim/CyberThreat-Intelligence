import time
import chromadb

def get_hybrid_context(query, window_minutes=60):
    client = chromadb.PersistentClient(path="./data/chroma_db")
    collection = client.get_collection(name="threat_intel")
    
    # Time-window calculation
    current_time = time.time()
    time_threshold = current_time - (window_minutes * 60)

    # Hybrid Search: Combining Vector and Keyword
    # Chroma handles the vector search, and we apply a metadata filter for time

    results = collection.query(
        query_texts=[query],
        n_results=10,
        where={"timestamp": {"$gte": time_threshold}}
    )
    
    if not results['documents'][0]:
        return "No threats detected in the last 60 minutes."
    
    context = "\n---\n".join(results['documents'][0])
    return context