from typing import List, Dict, Any, Optional
import math
import re
import logging
from app.rag.corpus import OFFICIAL_FINANCIAL_CORPUS
from app.rag.embeddings import get_embedding_provider, BaseEmbeddingProvider

logger = logging.getLogger("finpilot.rag.store")


def sanitize_document_text(text: str) -> str:
    """Neutralizes potential prompt injection phrases or malicious formatting in input documents."""
    text = re.sub(r"(?i)\bignore\s+(all\s+)?(previous|prior)\s+instructions\b", "[redacted instruction]", text)
    text = re.sub(r"(?i)\bsystem\s+prompt\b", "[redacted prompt]", text)
    text = re.sub(r"(?i)<script.*?>.*?</script>", "", text)
    return text.strip()


class RAGKnowledgeStore:
    """
    In-memory vector store abstraction with metadata filtering,
    hybrid retrieval (semantic vector + statutory keyword boost),
    relevance thresholding, and prompt-injection defense.
    """

    def __init__(self, embedding_provider: Optional[BaseEmbeddingProvider] = None):
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.chunks: List[Dict[str, Any]] = []
        self._is_ingested = False

    def ingest_corpus(self, force: bool = False):
        if self._is_ingested and not force:
            return

        self.chunks.clear()
        for doc in OFFICIAL_FINANCIAL_CORPUS:
            if doc.get("superseded_by"):
                continue  # Skip superseded legal documents

            cleaned_content = sanitize_document_text(doc["content"])
            full_text = f"{doc['title']}. {doc['citation']}. {cleaned_content}"
            embedding = self.embedding_provider.embed_text(full_text)

            chunk = {
                "id": doc["id"],
                "title": doc["title"],
                "publisher": doc["publisher"],
                "citation": doc["citation"],
                "url": doc["url"],
                "jurisdiction": doc["jurisdiction"],
                "topic": doc["topic"],
                "effective_date": doc["effective_date"],
                "content": cleaned_content,
                "tags": [t.lower() for t in doc.get("tags", [])],
                "embedding": embedding,
            }
            self.chunks.append(chunk)

        self._is_ingested = True
        logger.info(f"RAG Knowledge Store ingested {len(self.chunks)} statutory documents.")

    def search(
        self,
        query: str,
        top_k: int = 3,
        topic: Optional[str] = None,
        min_score: float = 0.08
    ) -> List[Dict[str, Any]]:
        if not self._is_ingested:
            self.ingest_corpus()

        query_clean = query.strip()
        query_vec = self.embedding_provider.embed_text(query_clean)
        query_tokens = set(re.findall(r"\w+", query_clean.lower()))

        scored_results = []

        for chunk in self.chunks:
            # Metadata filter by topic if specified
            if topic and chunk["topic"] != topic:
                continue

            # 1. Cosine similarity
            chunk_vec = chunk["embedding"]
            cos_sim = max(0.0, sum(q * c for q, c in zip(query_vec, chunk_vec)))

            # 2. Token overlap with document content
            doc_tokens = set(re.findall(r"\w+", chunk["content"].lower() + " " + chunk["title"].lower()))
            overlap_ratio = len(query_tokens.intersection(doc_tokens)) / max(1, len(query_tokens))

            # 3. Statutory tag boost
            chunk_tags = set(chunk["tags"])
            tag_overlap = len(query_tokens.intersection(chunk_tags))
            tag_boost = min(0.30, tag_overlap * 0.10)

            final_score = (cos_sim * 0.40) + (overlap_ratio * 0.45) + tag_boost

            if final_score >= min_score:
                scored_results.append({
                    "id": chunk["id"],
                    "title": chunk["title"],
                    "publisher": chunk["publisher"],
                    "citation": chunk["citation"],
                    "url": chunk["url"],
                    "jurisdiction": chunk["jurisdiction"],
                    "topic": chunk["topic"],
                    "effective_date": chunk["effective_date"],
                    "content": chunk["content"],
                    "score": round(float(final_score), 4)
                })

        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]


# Global singleton instance
rag_store = RAGKnowledgeStore()
