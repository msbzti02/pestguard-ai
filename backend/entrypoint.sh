#!/bin/bash
# ==============================================================
# PestGuard AI — Docker Entrypoint
# Builds ChromaDB index on first run if not present
# ==============================================================

set -e

echo "🌾 PestGuard AI — Starting..."

# Build RAG index if not already built
if [ ! -f "/app/data/chroma_db/chroma.sqlite3" ]; then
    echo "📚 First run: Building RAG vector index..."
    python /app/rag/build_index.py || echo "⚠️ Index build failed (will use mock responses)"
    echo "✅ RAG index ready"
else
    echo "✅ RAG index found, skipping build"
fi

# Start the server
echo "🚀 Starting Uvicorn server..."
exec "$@"
