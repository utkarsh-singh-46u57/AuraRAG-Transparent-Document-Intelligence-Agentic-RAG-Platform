from typing import List, Dict, Any, Optional, Tuple
import json
import logging
from rank_bm25 import BM25Okapi
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.models.domain import DocumentChunk, Citation
from app.services.embeddings import BaseEmbeddingProvider, get_embedding_provider
from app.config import settings

logger = logging.getLogger(__name__)

class ChromaVectorStore:
    """
    Persistent ChromaDB vector store coupled with BM25 Sparse Search and
    Reciprocal Rank Fusion (RRF) for high-precision hybrid retrieval.
    """

    def __init__(self, persist_directory: Optional[str] = None):
        persist_dir = persist_directory or str(settings.CHROMA_PERSIST_DIR)
        self.client = chromadb.PersistentClient(path=persist_dir)
        # Using a unified collection with session_id / document_id metadata filters
        self.collection = self.client.get_or_create_collection(
            name="aurarag_chunks",
            metadata={"hnsw:space": "cosine"}
        )
        # In-memory BM25 index cache per document_id: {doc_id: (BM25Okapi, List[DocumentChunk])}
        self._bm25_indices: Dict[str, Tuple[BM25Okapi, List[DocumentChunk]]] = {}

    def index_chunks(
        self,
        chunks: List[DocumentChunk],
        session_id: str,
        embedding_provider: Optional[BaseEmbeddingProvider] = None
    ) -> int:
        if not chunks:
            return 0

        doc_id = chunks[0].document_id
        provider = embedding_provider or get_embedding_provider()

        texts = [c.text for c in chunks]
        ids = [f"{session_id}_{c.chunk_id}" for c in chunks]
        embeddings = provider.embed_documents(texts)

        metadatas = []
        for c in chunks:
            metadatas.append({
                "session_id": session_id,
                "document_id": c.document_id,
                "chunk_id": c.chunk_id,
                "page_number": c.page_number,
                "paragraph_number": c.paragraph_number,
                "section_heading": c.section_heading or "",
                "bbox_json": json.dumps(c.bbox) if c.bbox else "[]",
                "char_count": c.char_count,
            })

        # Upsert into ChromaDB
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        # Build BM25 index for sparse search
        tokenized_corpus = [c.text.lower().split() for c in chunks]
        bm25 = BM25Okapi(tokenized_corpus)
        self._bm25_indices[doc_id] = (bm25, chunks)

        logger.info(f"Indexed {len(chunks)} chunks for document {doc_id} in session {session_id}")
        return len(chunks)

    def hybrid_search(
        self,
        query: str,
        document_id: str,
        session_id: Optional[str] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.65,
        embedding_provider: Optional[BaseEmbeddingProvider] = None
    ) -> List[Citation]:
        """
        Executes dense vector search + sparse BM25 search and merges via Reciprocal Rank Fusion.
        """
        provider = embedding_provider or get_embedding_provider()
        
        # 1. Dense Search via ChromaDB
        query_embedding = provider.embed_query(query)
        if session_id:
            where_filter: Dict[str, Any] = {
                "$and": [
                    {"document_id": {"$eq": document_id}},
                    {"session_id": {"$eq": session_id}}
                ]
            }
        else:
            where_filter: Dict[str, Any] = {"document_id": {"$eq": document_id}}

        # Query top 20 dense candidates
        dense_results = self.collection.query(
            query_embeddings=[query_embedding],
            where=where_filter,
            n_results=min(20, max(top_k * 3, 10))
        )

        dense_ranked_ids: List[str] = []
        dense_scores: Dict[str, float] = {}
        chunk_lookup: Dict[str, dict] = {}

        if dense_results and dense_results["ids"] and len(dense_results["ids"][0]) > 0:
            for rank, (doc_uid, distance, text, meta) in enumerate(zip(
                dense_results["ids"][0],
                dense_results["distances"][0],
                dense_results["documents"][0],
                dense_results["metadatas"][0]
            )):
                chunk_id = meta["chunk_id"]
                dense_ranked_ids.append(chunk_id)
                # Chroma cosine distance is in [0, 2], similarity is 1 - distance
                similarity = max(0.0, 1.0 - (distance / 2.0))
                dense_scores[chunk_id] = similarity
                chunk_lookup[chunk_id] = {
                    "text": text,
                    "metadata": meta,
                    "dense_similarity": similarity
                }

        # 2. Sparse Search via BM25
        bm25_ranked_ids: List[str] = []
        if document_id in self._bm25_indices:
            bm25, doc_chunks = self._bm25_indices[document_id]
            tokenized_query = query.lower().split()
            scores = bm25.get_scores(tokenized_query)
            
            # Rank chunks by BM25 score
            scored_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
            for idx in scored_indices[:min(20, max(top_k * 3, 10))]:
                if scores[idx] > 0.0:
                    c = doc_chunks[idx]
                    bm25_ranked_ids.append(c.chunk_id)
                    if c.chunk_id not in chunk_lookup:
                        chunk_lookup[c.chunk_id] = {
                            "text": c.text,
                            "metadata": {
                                "chunk_id": c.chunk_id,
                                "page_number": c.page_number,
                                "paragraph_number": c.paragraph_number,
                                "section_heading": c.section_heading or "",
                                "bbox_json": json.dumps(c.bbox) if c.bbox else "[]"
                            },
                            "dense_similarity": 0.5
                        }

        # 3. Reciprocal Rank Fusion (RRF)
        # RRF_Score = 1/(k + Rank_dense) + 1/(k + Rank_bm25)
        rrf_k = settings.RRF_K
        rrf_scores: Dict[str, float] = {}

        # Dense ranks
        for rank, chk_id in enumerate(dense_ranked_ids):
            rrf_scores[chk_id] = rrf_scores.get(chk_id, 0.0) + (1.0 / (rrf_k + rank + 1))

        # BM25 ranks
        for rank, chk_id in enumerate(bm25_ranked_ids):
            rrf_scores[chk_id] = rrf_scores.get(chk_id, 0.0) + (1.0 / (rrf_k + rank + 1))

        # Sort by final RRF score
        sorted_chunks = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)

        citations: List[Citation] = []
        for chk_id, score in sorted_chunks[:top_k]:
            data = chunk_lookup.get(chk_id)
            if not data:
                continue

            # Normalized confidence score between 0.60 and 0.99
            dense_sim = data.get("dense_similarity", 0.70)
            confidence_score = round(max(dense_sim, 0.66 + min(score * 5.0, 0.33)), 2)

            # Filter by threshold unless explicit match
            if confidence_score < similarity_threshold and chk_id not in bm25_ranked_ids[:2]:
                continue

            meta = data["metadata"]
            bbox_raw = meta.get("bbox_json", "[]")
            bbox = json.loads(bbox_raw) if isinstance(bbox_raw, str) else bbox_raw

            citations.append(
                Citation(
                    chunk_id=chk_id,
                    page_number=int(meta.get("page_number", 1)),
                    paragraph_number=int(meta.get("paragraph_number", 0)),
                    score=confidence_score,
                    text=data["text"],
                    bbox=bbox if bbox else None,
                    section_heading=meta.get("section_heading") or None
                )
            )

        return citations

    def delete_document(self, document_id: str, session_id: Optional[str] = None) -> int:
        """Deletes all chunks associated with a document_id."""
        if session_id:
            where_filter: Dict[str, Any] = {
                "$and": [
                    {"document_id": {"$eq": document_id}},
                    {"session_id": {"$eq": session_id}}
                ]
            }
        else:
            where_filter: Dict[str, Any] = {"document_id": {"$eq": document_id}}

        try:
            self.collection.delete(where=where_filter)
        except Exception as e:
            logger.warning(f"Error during collection.delete for {document_id}: {str(e)}")

        if document_id in self._bm25_indices:
            del self._bm25_indices[document_id]

        logger.info(f"Deleted vector chunks for document {document_id}")
        return 1

vector_store = ChromaVectorStore()
