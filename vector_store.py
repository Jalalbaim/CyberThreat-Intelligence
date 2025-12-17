import chromadb
from chromadb.config import Settings as ChromaSettings

class VectorStore:
    def __init__(self, persist_dir: str, collection_name: str):
        self.client = chromadb.Client(
            ChromaSettings(
                is_persistent=True,              # 🔑 THIS FIXES EVERYTHING
                persist_directory=persist_dir,
                anonymized_telemetry=False
            )
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def upsert(self, ids, embeddings, metadatas, documents):
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )

    def query(self, query_embeddings, top_k=5):
        res = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=top_k,
            include=["distances", "metadatas", "documents"]
        )

        results = []
        if res and res["ids"]:
            for i in range(len(res["ids"][0])):
                results.append({
                    "id": res["ids"][0][i],
                    "document": res["documents"][0][i],
                    "metadata": res["metadatas"][0][i],
                    "distance": res["distances"][0][i],
                })
        return results
