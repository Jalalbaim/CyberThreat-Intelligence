import time
import re
import chromadb
import json 
from rank_bm25 import BM25Okapi

def get_hybrid_context(query, window_minutes=60, top_k=10, vector_weight=0.7):
    """
    Hybrid retrieval: combine vector (embedding) similarity with BM25 lexical search.
    - vector_weight is weight given to the vector score (0..1). BM25 weight = 1 - vector_weight.
    - top_k number of results to return.
    """

    client = chromadb.PersistentClient(path="./data/chroma_db")
    collection = client.get_collection(name="threat_intel")

    current_time = time.time()
    time_threshold = current_time - (window_minutes * 60)

    # --- Vector search ---
    vector_res = collection.query(
        query_texts=[query],
        n_results=top_k,
        where={"timestamp": {"$gte": time_threshold}},
        include=["documents", "metadatas", "distances"]
    )
 
    vec_ids = vector_res.get("ids", [[]])[0]
    vec_docs = vector_res.get("documents", [[]])[0]
    vec_distances = vector_res.get("distances", [[]])[0]

    # vector score dict 
    vector_scores = {}
    if vec_distances:
        max_d = max(vec_distances)
        min_d = min(vec_distances)
        for _id, d in zip(vec_ids, vec_distances):
            if max_d == min_d:
                s = 1.0
            else:
                s = 1.0 - ((d - min_d) / (max_d - min_d))
            vector_scores[_id] = float(s)
    else:
        vector_scores = {}

    with open("./data/threat_intel_vector_scores.json", "w") as f:
        json.dump(vector_scores, f)

    # --- BM25 search ---
    all_data = collection.get(
        where={"timestamp": {"$gte": time_threshold}},
        include=["documents", "metadatas"]
    )

    ids = all_data.get("ids", [])
    docs = all_data.get("documents", [])
    if ids and isinstance(ids, list) and len(ids) > 0 and isinstance(ids[0], list):
        ids = ids[0]
    if docs and isinstance(docs, list) and len(docs) > 0 and isinstance(docs[0], list):
        docs = docs[0]

    if not docs:
        return "No threats detected in the last {} minutes.".format(window_minutes)

    def tokenize(text):
        """Tokenize text for BM25"""
        tokens = re.findall(r"\w+", (text or "").lower())
        return tokens

    # Tokenize
    tokenized_docs = [tokenize(doc) for doc in docs]

    bm25 = BM25Okapi(tokenized_docs)
    
    # Tokenize query
    tokenized_query = tokenize(query)

    bm25_scores_raw = bm25.get_scores(tokenized_query)

    bm25_scores = {}
    if len(bm25_scores_raw) > 0:
        max_score = max(bm25_scores_raw)
        min_score = min(bm25_scores_raw)
        
        for _id, score in zip(ids, bm25_scores_raw):
            if max_score == min_score:
                normalized_score = 1.0 if max_score > 0 else 0.0
            else:
                normalized_score = (score - min_score) / (max_score - min_score)
            bm25_scores[_id] = float(normalized_score)
    else:
        bm25_scores = {_id: 0.0 for _id in ids}
    
    with open("./data/bm25_scores.json", "w") as f:
        json.dump(bm25_scores, f)

    # --- Ranker (combine vector + BM25) ---
    combined_scores = {}
    all_candidate_ids = set(list(vector_scores.keys()) + list(bm25_scores.keys()))

    for _id in all_candidate_ids:
        v = vector_scores.get(_id, 0.0)
        b = bm25_scores.get(_id, 0.0)
        combined = vector_weight * v + (1.0 - vector_weight) * b
        combined_scores[_id] = combined

    # Pick top_k
    ranked = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    ranked_ids = [r[0] for r in ranked]

    # id -> document mapping
    id_to_doc = dict(zip(ids, docs))
    id_to_doc.update(dict(zip(vec_ids, vec_docs)))

    ranked_docs = [id_to_doc.get(_id, "") for _id in ranked_ids if id_to_doc.get(_id, "")]

    if not ranked_docs:
        return "No relevant threats found in the last {} minutes.".format(window_minutes)

    context = "\n---\n".join(ranked_docs)
    return context