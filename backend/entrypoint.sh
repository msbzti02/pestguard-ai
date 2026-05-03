#!/bin/bash
# ==============================================================
# PestGuard AI — Docker Entrypoint
# Uses pre-built ChromaDB index (included in image)
# ==============================================================

set -e

echo "PestGuard AI — Starting..."

# Check if RAG index exists
if [ -f "/app/data/chroma_db/chroma.sqlite3" ]; then
    echo "RAG index found, ready to serve"
else
    echo "Building RAG vector index..."
    python /app/rag/build_index.py || echo "Index build failed (will use mock responses)"
    echo "RAG index ready"
fi

# Start the server
echo "Starting Uvicorn server..."
exec "$@"
