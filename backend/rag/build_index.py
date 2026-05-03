"""
RAG Pipeline — Document Indexer (build_index.py)
=================================================
Loads all documents from data/documents/, splits them into chunks,
generates vector embeddings, and stores everything in ChromaDB.

Run this script ONCE to build the index. Re-run if you add new documents.

Usage:
    python rag/build_index.py

What this does step by step:
    1. Scans data/documents/ for PDF and TXT files
    2. Extracts text from each document
    3. Splits text into overlapping chunks (~500 tokens each)
    4. Generates vector embeddings using sentence-transformers (FREE, runs locally)
    5. Stores all chunks + embeddings in a ChromaDB database on disk
    6. The database persists at data/chroma_db/ for use by the retriever
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path so we can run from backend/
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chromadb import PersistentClient
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


# ============================================================================
# Configuration
# ============================================================================
DOCS_DIR = Path(__file__).parent.parent / "data" / "documents"
CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma_db"
COLLECTION_NAME = "pest_management_knowledge"

# Embedding model — runs locally, no API key needed
# all-MiniLM-L6-v2 is fast, lightweight (~80MB), and good quality
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Chunk settings
CHUNK_SIZE = 500       # ~500 characters per chunk
CHUNK_OVERLAP = 100    # 100 character overlap between chunks (preserves context)


# ============================================================================
# Document Loading
# ============================================================================
def load_all_documents(docs_dir: Path) -> list:
    """
    Load every PDF and TXT file from the documents directory.
    Returns a list of LangChain Document objects with metadata.
    """
    all_docs = []
    supported_files = list(docs_dir.glob("*.pdf")) + list(docs_dir.glob("*.txt"))

    if not supported_files:
        print(f"ERROR: No PDF or TXT files found in {docs_dir}")
        sys.exit(1)

    print(f"Found {len(supported_files)} document files\n")

    for filepath in sorted(supported_files):
        filename = filepath.name
        try:
            if filepath.suffix.lower() == ".pdf":
                loader = PyPDFLoader(str(filepath))
                docs = loader.load()
                # Add source filename to each page's metadata
                for doc in docs:
                    doc.metadata["source_file"] = filename
                    doc.metadata["file_type"] = "pdf"
                print(f"  PDF  {filename}: {len(docs)} pages loaded")

            elif filepath.suffix.lower() == ".txt":
                loader = TextLoader(str(filepath), encoding="utf-8")
                docs = loader.load()
                for doc in docs:
                    doc.metadata["source_file"] = filename
                    doc.metadata["file_type"] = "txt"
                print(f"  TXT  {filename}: {len(docs)} document(s) loaded")

            else:
                continue

            all_docs.extend(docs)

        except Exception as e:
            print(f"  WARN Skipping {filename}: {e}")

    return all_docs


# ============================================================================
# Text Splitting / Chunking
# ============================================================================
def chunk_documents(documents: list, chunk_size: int, chunk_overlap: int) -> list:
    """
    Split documents into overlapping chunks for better retrieval.

    Why chunk?
        - LLMs have context limits — we can't feed entire PDFs
        - Smaller chunks = more precise retrieval matches
        - Overlap ensures no information is lost at chunk boundaries

    Why 500 chars with 100 overlap?
        - 500 chars ≈ 70-100 words ≈ a focused paragraph
        - 100 char overlap preserves context across boundaries
        - These values work well for agricultural/technical documents
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=[
            "\n\n",     # Double newline (paragraph break) — highest priority
            "\n",       # Single newline
            ". ",       # Sentence end
            ", ",       # Clause break
            " ",        # Word break
            "",         # Character break (last resort)
        ],
        is_separator_regex=False,
    )

    chunks = splitter.split_documents(documents)
    return chunks


# ============================================================================
# Embedding & Storage in ChromaDB
# ============================================================================
def build_chroma_index(chunks: list, chroma_dir: Path, collection_name: str, model_name: str):
    """
    Generate embeddings for all chunks and store them in ChromaDB.

    ChromaDB stores:
        - The chunk text (for retrieval)
        - The vector embedding (for similarity search)
        - Metadata (source file, page number, etc.)

    The embedding model runs LOCALLY — no API key needed.
    """
    # Initialize embedding function
    print(f"\nLoading embedding model: {model_name}")
    print("  (First run downloads ~80MB model — subsequent runs use cache)\n")
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=model_name)

    # Create or overwrite ChromaDB
    chroma_dir.mkdir(parents=True, exist_ok=True)
    client = PersistentClient(path=str(chroma_dir))

    # Delete existing collection if it exists (clean rebuild)
    try:
        client.delete_collection(collection_name)
        print(f"  Deleted existing collection: {collection_name}")
    except Exception:
        pass

    # Create fresh collection
    collection = client.create_collection(
        name=collection_name,
        embedding_function=embedding_fn,
        metadata={"description": "Agricultural pest management knowledge base for RAG"}
    )

    # Add chunks in batches (ChromaDB has a batch size limit)
    BATCH_SIZE = 100
    total = len(chunks)

    print(f"\nIndexing {total} chunks into ChromaDB...")
    print(f"  Collection: {collection_name}")
    print(f"  Storage: {chroma_dir}\n")

    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]

        ids = [f"chunk_{i + j}" for j in range(len(batch))]
        texts = [chunk.page_content for chunk in batch]
        metadatas = [
            {
                "source_file": chunk.metadata.get("source_file", "unknown"),
                "file_type": chunk.metadata.get("file_type", "unknown"),
                "page": chunk.metadata.get("page", 0),
                "chunk_index": i + j,
            }
            for j, chunk in enumerate(batch)
        ]

        collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
        )

        progress = min(i + BATCH_SIZE, total)
        pct = (progress / total) * 100
        print(f"  [{progress}/{total}] {pct:.0f}% indexed")

    print(f"\nDone. Collection has {collection.count()} chunks stored.")
    return collection


# ============================================================================
# Verification — Test the index with sample queries
# ============================================================================
def verify_index(collection, embedding_fn):
    """
    Run test queries to make sure the RAG retrieval is working correctly.
    """
    test_queries = [
        "How to control aphids on crops?",
        "What pesticides are safe for rice stem borer?",
        "Weather conditions for safe pesticide spraying",
        "Biological control methods for corn borer",
        "Locust swarm management and monitoring",
    ]

    print("\n" + "=" * 60)
    print("  VERIFICATION — Testing retrieval quality")
    print("=" * 60)

    all_passed = True

    for query in test_queries:
        results = collection.query(
            query_texts=[query],
            n_results=3,
        )

        docs = results["documents"][0]
        sources = [m["source_file"] for m in results["metadatas"][0]]

        # Check if we got results
        if not docs or len(docs[0]) < 20:
            print(f"\n  FAIL: '{query}'")
            print(f"         No relevant results found!")
            all_passed = False
        else:
            print(f"\n  PASS: '{query}'")
            print(f"         Sources: {', '.join(set(sources))}")
            print(f"         Top result: {docs[0][:120]}...")

    if all_passed:
        print("\n  All 5 test queries returned relevant results!")
    else:
        print("\n  WARNING: Some queries did not return good results.")
        print("  Consider adding more documents to improve coverage.")

    return all_passed


# ============================================================================
# Main
# ============================================================================
def main():
    print("=" * 60)
    print("  RAG Pipeline — Building Vector Index")
    print("=" * 60)
    print(f"\n  Documents: {DOCS_DIR}")
    print(f"  Database:  {CHROMA_DIR}")
    print(f"  Model:     {EMBEDDING_MODEL}")
    print(f"  Chunk:     {CHUNK_SIZE} chars, {CHUNK_OVERLAP} overlap\n")

    start_time = time.time()

    # Step 1: Load documents
    print("-" * 40)
    print("STEP 1: Loading documents")
    print("-" * 40)
    documents = load_all_documents(DOCS_DIR)
    print(f"\nTotal: {len(documents)} document pages/sections loaded")

    # Step 2: Chunk documents
    print(f"\n{'-' * 40}")
    print("STEP 2: Chunking documents")
    print("-" * 40)
    chunks = chunk_documents(documents, CHUNK_SIZE, CHUNK_OVERLAP)
    print(f"  Created {len(chunks)} chunks from {len(documents)} document sections")

    # Show chunk stats
    lengths = [len(c.page_content) for c in chunks]
    print(f"  Average chunk length: {sum(lengths)//len(lengths)} characters")
    print(f"  Min: {min(lengths)}, Max: {max(lengths)} characters")

    # Step 3: Build index
    print(f"\n{'-' * 40}")
    print("STEP 3: Embedding and indexing")
    print("-" * 40)
    collection = build_chroma_index(chunks, CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL)

    # Step 4: Verify
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    verify_index(collection, embedding_fn)

    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"  BUILD COMPLETE in {elapsed:.1f} seconds")
    print(f"  {collection.count()} chunks indexed and ready for retrieval")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
