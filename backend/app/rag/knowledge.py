from typing import List, Dict, Any, Optional
from app.rag.store import rag_store
from app.rag.corpus import OFFICIAL_FINANCIAL_CORPUS

# Backward compatibility export
APPROVED_KNOWLEDGE_DOCUMENTS = OFFICIAL_FINANCIAL_CORPUS


class KnowledgeRetriever:
    """
    RAG retrieval engine matching user financial queries against approved statutory source documents
    using semantic vector search with keyword/tag boosting and relevance thresholds.
    """

    @classmethod
    def search(
        cls,
        query: str,
        top_k: int = 3,
        topic: Optional[str] = None,
        min_score: float = 0.08
    ) -> List[Dict[str, Any]]:
        return rag_store.search(query=query, top_k=top_k, topic=topic, min_score=min_score)
