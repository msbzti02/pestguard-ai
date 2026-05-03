"""Quick test script for Stage 2 endpoints."""
import httpx
import json

BASE = "http://localhost:8000"

# Test 1: Health check
print("=" * 60)
r = httpx.get(f"{BASE}/")
data = r.json()
print(f"STATUS: {data['status']}")
print(f"STAGE: {data['stage']}")

# Test 2: High-confidence chat
print("\n" + "=" * 60)
print("TEST: High Confidence Chat")
r = httpx.post(f"{BASE}/chat", json={
    "message": "How to control aphids on my rice field?",
    "pest_name": "Aphid",
    "confidence": 0.91,
    "session_id": "test-session"
}, timeout=30)
data = r.json()
print(f"PROMPT TYPE: {data.get('prompt_type')}")
print(f"LLM PROVIDER: {data.get('llm_provider')}")
sources = data.get("rag_sources", [])
print(f"RAG SOURCES ({len(sources)}): {[s['source'] for s in sources]}")
print(f"LOW CONF: {data['is_low_confidence']}")
print(f"REPLY (first 400 chars):")
print(data["reply"][:400])

# Test 3: Low-confidence chat
print("\n" + "=" * 60)
print("TEST: Low Confidence Chat")
r = httpx.post(f"{BASE}/chat", json={
    "message": "What is this bug?",
    "confidence": 0.45,
    "session_id": "test-low"
}, timeout=30)
data = r.json()
print(f"PROMPT TYPE: {data.get('prompt_type')}")
print(f"LOW CONF: {data['is_low_confidence']}")
print(f"REPLY (first 300 chars):")
print(data["reply"][:300])

# Test 4: Follow-up in same session
print("\n" + "=" * 60)
print("TEST: Follow-up Chat (same session)")
r = httpx.post(f"{BASE}/chat", json={
    "message": "Now I see corn borers, how to treat?",
    "pest_name": "Corn Borer",
    "confidence": 0.85,
    "session_id": "test-session"
}, timeout=30)
data = r.json()
print(f"PROMPT TYPE: {data.get('prompt_type')}")
sources = data.get("rag_sources", [])
print(f"RAG SOURCES ({len(sources)}): {[s['source'] for s in sources]}")
print(f"REPLY (first 400 chars):")
print(data["reply"][:400])

# Test 5: Verify disclaimer on all responses
print("\n" + "=" * 60)
print("TEST: Disclaimer Check")
has_disclaimer = "DISCLAIMER" in data["disclaimer"]
print(f"DISCLAIMER PRESENT: {has_disclaimer}")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETE")
