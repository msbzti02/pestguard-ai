"""
RAG Pipeline — Retriever (retriever.py)
========================================
Connects to the ChromaDB vector database and retrieves relevant
document chunks based on a user query.

This is the bridge between the user's question and the LLM's knowledge.

How it works:
    1. User asks: "How to treat aphids on rice?"
    2. The query is converted to a vector embedding
    3. ChromaDB finds the 5 most similar document chunks
    4. Those chunks are returned as context for the LLM

Usage:
    from rag.retriever import PestKnowledgeRetriever

    retriever = PestKnowledgeRetriever()
    context = retriever.retrieve("How to treat aphids?")
    print(context)
"""

from pathlib import Path
from chromadb import PersistentClient
try:
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
except ImportError:
    SentenceTransformerEmbeddingFunction = None


# ============================================================================
# Configuration — must match build_index.py settings
# ============================================================================
CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma_db"
COLLECTION_NAME = "pest_management_knowledge"
EMBEDDING_MODEL = "all-mpnet-base-v2"


class PestKnowledgeRetriever:
    """
    Retrieves relevant agricultural pest management knowledge from the
    ChromaDB vector database.

    Methods:
        retrieve(query, top_k=5) → str
            Returns formatted context string with relevant document chunks.

        retrieve_with_sources(query, top_k=5) → dict
            Returns chunks + metadata (source files, relevance scores).

        is_ready() → bool
            Checks if the ChromaDB index exists and has data.
    """

    def __init__(self, chroma_dir: Path = CHROMA_DIR,
                 collection_name: str = COLLECTION_NAME,
                 model_name: str = EMBEDDING_MODEL):
        """
        Initialize the retriever by connecting to the existing ChromaDB.

        Args:
            chroma_dir: Path to the ChromaDB storage directory
            collection_name: Name of the ChromaDB collection
            model_name: Sentence-transformer model for query embedding
        """
        self.chroma_dir = chroma_dir
        self.collection_name = collection_name
        self.model_name = model_name

        # These are initialized lazily on first use
        self._client = None
        self._collection = None
        self._embedding_fn = None

    def _ensure_loaded(self):
        """Lazy-load the ChromaDB connection and embedding model."""
        if self._collection is not None:
            return

        if not self.chroma_dir.exists():
            raise FileNotFoundError(
                f"ChromaDB not found at {self.chroma_dir}. "
                "Run 'python rag/build_index.py' first to build the index."
            )

        # Try loading sentence-transformers embedding function
        # Falls back to default if not installed (deploy mode)
        try:
            self._embedding_fn = SentenceTransformerEmbeddingFunction(
                model_name=self.model_name
            )
        except Exception:
            self._embedding_fn = None  # Use chromadb default

        self._client = PersistentClient(path=str(self.chroma_dir))
        if self._embedding_fn:
            self._collection = self._client.get_collection(
                name=self.collection_name,
                embedding_function=self._embedding_fn,
            )
        else:
            self._collection = self._client.get_collection(
                name=self.collection_name,
            )

    def is_ready(self) -> bool:
        """Check if the ChromaDB index exists and contains data."""
        try:
            self._ensure_loaded()
            return self._collection.count() > 0
        except BaseException:
            return False

    def retrieve(self, query: str, top_k: int = 5) -> str:
        """
        Retrieve relevant document chunks and return as a formatted string.

        This is the main method used by the LLM agent. It returns a single
        string containing the most relevant agricultural knowledge, ready
        to be injected into the LLM prompt.

        Args:
            query: The user's question or the pest context string
            top_k: Number of chunks to retrieve (default: 5)

        Returns:
            A formatted string with numbered chunks and source citations.
            Returns a fallback message if no relevant results are found.

        Example:
            >>> retriever = PestKnowledgeRetriever()
            >>> context = retriever.retrieve("How to control aphids?")
            >>> print(context)
            [1] (pest_management_aphids.txt)
            Aphid identification, chemical control...
            ---
            [2] (FAO_Integrated_Pest_Management.pdf, p.23)
            Integrated pest management approaches include...
        """
        self._ensure_loaded()

        results = self._collection.query(
            query_texts=[query],
            n_results=top_k,
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0] if results.get("distances") else [None] * len(documents)

        if not documents or len(documents) == 0:
            return (
                "No relevant agricultural knowledge found in the database. "
                "The recommendation will be based on the LLM's general knowledge only. "
                "Note: Recommendations without RAG grounding may be less accurate."
            )

        # Format chunks with source citations
        formatted_chunks = []
        for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
            source = meta.get("source_file", "unknown")
            page = meta.get("page", None)

            # Build citation
            if page and page > 0:
                citation = f"({source}, p.{page})"
            else:
                citation = f"({source})"

            # Clean up the text
            clean_text = doc.strip()
            if len(clean_text) < 10:
                continue

            formatted_chunks.append(f"[{i + 1}] {citation}\n{clean_text}")

        if not formatted_chunks:
            return "No sufficiently relevant passages found in the knowledge base."

        return "\n---\n".join(formatted_chunks)

    def retrieve_with_rerank(self, query: str, top_k: int = 5, candidate_k: int = 15) -> str:
        """
        Two-stage retrieval:
          1. Fetch candidate_k candidates via vector similarity (broad recall)
          2. Re-rank by keyword overlap + distance scoring (precision)
          3. Return top_k best results
        """
        self._ensure_loaded()

        # Stage 1: Broad retrieval
        results = self._collection.query(
            query_texts=[query],
            n_results=candidate_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        if not documents:
            return "No relevant agricultural knowledge found in the database."

        # Stage 2: Re-rank
        query_terms = set(query.lower().split())
        scored = []

        for doc, meta, dist in zip(documents, metadatas, distances):
            # Base score: inverse distance (lower distance = higher score)
            base_score = 1.0 / (1.0 + dist) if dist is not None else 1.0

            # Keyword bonus: how many query terms appear in the chunk
            doc_lower = doc.lower()
            keyword_hits = sum(1 for term in query_terms if term in doc_lower)
            keyword_bonus = keyword_hits * 0.1

            # Length bonus: prefer chunks with more content (more informative)
            length_bonus = min(len(doc) / 2000, 0.15)

            # Section bonus: prefer chunks that have structured sections
            section_indicators = ["MANAGEMENT:", "CONTROL:", "CHEMICAL", "BIOLOGICAL",
                                  "TREATMENT", "THRESHOLD", "IDENTIFICATION"]
            section_bonus = 0.1 if any(s in doc.upper() for s in section_indicators) else 0

            final_score = base_score + keyword_bonus + length_bonus + section_bonus
            scored.append((doc, meta, dist, final_score))

        # Sort by final score descending
        scored.sort(key=lambda x: x[3], reverse=True)

        # Take top_k
        formatted_chunks = []
        for i, (doc, meta, dist, score) in enumerate(scored[:top_k]):
            source = meta.get("source_file", "unknown")
            page = meta.get("page", None)
            citation = f"({source}, p.{page})" if page and page > 0 else f"({source})"
            clean_text = doc.strip()
            if len(clean_text) < 10:
                continue
            formatted_chunks.append(f"[{i + 1}] {citation} [relevance: {score:.2f}]\n{clean_text}")

        return "\n---\n".join(formatted_chunks) if formatted_chunks else "No relevant passages found."

    def retrieve_filtered(self, query: str, pest_filter: str = None,
                          topic_filter: str = None, top_k: int = 5) -> str:
        """
        Retrieve with optional metadata filtering.
        Example: retrieve_filtered("how to control", pest_filter="aphid", topic_filter="chemical_control")
        """
        self._ensure_loaded()

        where_filter = {}
        if pest_filter:
            where_filter["pest_tags"] = {"$contains": pest_filter.lower()}
        if topic_filter:
            where_filter["topic"] = topic_filter

        kwargs = {
            "query_texts": [query],
            "n_results": top_k,
        }
        if where_filter:
            kwargs["where"] = where_filter

        results = self._collection.query(**kwargs)
        
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0] if results.get("distances") else [None] * len(documents)

        if not documents or len(documents) == 0:
            return "No relevant passages found with the specified filters."

        formatted_chunks = []
        for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
            source = meta.get("source_file", "unknown")
            page = meta.get("page", None)
            citation = f"({source}, p.{page})" if page and page > 0 else f"({source})"
            clean_text = doc.strip()
            if len(clean_text) < 10:
                continue
            formatted_chunks.append(f"[{i + 1}] {citation}\n{clean_text}")

        return "\n---\n".join(formatted_chunks) if formatted_chunks else "No relevant passages found."

    def expand_query(self, original_query: str, pest_name: str = None) -> str:
        """
        Expand a user query with agricultural synonyms and technical terms
        to improve retrieval recall.
        """
        expansions = {
            "kill": "control manage treat eliminate",
            "bug": "insect pest arthropod",
            "spray": "pesticide application treatment chemical foliar",
            "organic": "biological cultural natural IPM non-chemical",
            "safe": "safety precaution protective threshold timing",
            "when": "timing threshold growth stage application schedule",
            "prevent": "prevention cultural control prophylactic resistant variety",
        }

        expanded = original_query
        for trigger, expansion in expansions.items():
            if trigger in original_query.lower():
                expanded += f" {expansion}"

        if pest_name and pest_name not in ("Unknown", "Uncertain"):
            expanded += f" {pest_name} management control"

        return expanded

    def retrieve_with_sources(self, query: str, top_k: int = 5) -> dict:
        """
        Retrieve chunks with full metadata — used for debugging and display.

        Returns:
            dict with keys:
                - chunks: list of {text, source_file, page, relevance_score}
                - query: the original query
                - total_in_db: total chunks in the database
        """
        self._ensure_loaded()

        results = self._collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0] if results.get("distances") else [0] * len(results["documents"][0]),
        ):
            chunks.append({
                "text": doc.strip(),
                "source_file": meta.get("source_file", "unknown"),
                "file_type": meta.get("file_type", "unknown"),
                "page": meta.get("page", 0),
                "distance": round(dist, 4) if dist else None,
            })

        return {
            "chunks": chunks,
            "query": query,
            "total_in_db": self._collection.count(),
        }

    def get_stats(self) -> dict:
        """Return statistics about the vector database."""
        self._ensure_loaded()
        return {
            "collection_name": self.collection_name,
            "total_chunks": self._collection.count(),
            "embedding_model": self.model_name,
            "storage_path": str(self.chroma_dir),
        }


# ============================================================================
# Quick test — run this file directly to verify the retriever works
# ============================================================================
if __name__ == "__main__":
    print("Testing PestKnowledgeRetriever...\n")

    retriever = PestKnowledgeRetriever()

    if not retriever.is_ready():
        print("ERROR: ChromaDB index not found!")
        print("Run 'python rag/build_index.py' first.")
        exit(1)

    stats = retriever.get_stats()
    print(f"Database: {stats['total_chunks']} chunks indexed\n")

    # Test queries
    queries = [
        "How to control aphids on rice?",
        "Safe weather conditions for spraying pesticides",
        "Biological control methods for corn borer",
        "What is the confidence threshold for pest predictions?",
        "Locust management and monitoring techniques",
    ]

    for q in queries:
        print(f"Query: {q}")
        result = retriever.retrieve(q, top_k=3)
        # Show first 200 chars of result
        print(f"Result: {result[:200]}...\n")

    print("Retriever is working correctly!")
