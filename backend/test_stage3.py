"""Stage 3 Full Test Suite — VLM + Weather + Agent."""
import httpx
import json

BASE = "http://localhost:8000"

# ========================================
# Test 1: Health check — verify Stage 3
# ========================================
print("=" * 60)
print("TEST 1: Health Check")
r = httpx.get(f"{BASE}/")
data = r.json()
print(f"  STATUS: {data['status']}")
print(f"  STAGE:  {data['stage']}")
print(f"  VLM:    {data.get('vlm', 'N/A')}")
print(f"  WEATHER: {data.get('weather', 'N/A')}")

# ========================================
# Test 2: Weather — real or mock?
# ========================================
print("\n" + "=" * 60)
print("TEST 2: Weather (Istanbul)")
r = httpx.get(f"{BASE}/weather/41.0/29.0", timeout=15)
w = r.json()
print(f"  Temp: {w['temperature']}°C")
print(f"  Wind: {w['wind_speed']} km/h")
print(f"  Rain: {w['rain_probability']}%")
print(f"  Condition: {w['condition']}")
print(f"  Safe to spray: {w['safe_to_spray']}")
print(f"  Alerts: {w['alerts']}")
print(f"  Mock: {w['is_mock']}")
print(f"  Disclaimer: {w['disclaimer'][:80]}...")

# ========================================
# Test 3: Chat with weather context
# ========================================
print("\n" + "=" * 60)
print("TEST 3: Chat with Weather Context")
r = httpx.post(f"{BASE}/chat", json={
    "message": "How to treat aphids on my rice field?",
    "pest_name": "Aphid",
    "confidence": 0.91,
    "session_id": "stage3-test",
    "lat": 41.0,
    "lon": 29.0,
}, timeout=30)
data = r.json()
print(f"  Prompt type: {data.get('prompt_type')}")
print(f"  LLM provider: {data.get('llm_provider')}")
print(f"  Weather warning: {data.get('weather_warning')}")
sources = data.get("rag_sources", [])
print(f"  RAG sources ({len(sources)}): {[s['source'] for s in sources]}")
print(f"  Reply (first 300 chars):")
print(f"  {data['reply'][:300]}")

# ========================================
# Test 4: Low confidence
# ========================================
print("\n" + "=" * 60)
print("TEST 4: Low Confidence")
r = httpx.post(f"{BASE}/chat", json={
    "message": "What pest is this?",
    "confidence": 0.35,
    "session_id": "stage3-low",
}, timeout=30)
data = r.json()
print(f"  Low confidence: {data['is_low_confidence']}")
print(f"  Prompt type: {data.get('prompt_type')}")
print(f"  Reply (first 200 chars):")
print(f"  {data['reply'][:200]}")

# ========================================
# Test 5: Disclaimer on all
# ========================================
print("\n" + "=" * 60)
print("TEST 5: Disclaimer Verification")
print(f"  Has DISCLAIMER: {'DISCLAIMER' in data['disclaimer']}")

print("\n" + "=" * 60)
print("ALL STAGE 3 TESTS COMPLETE ✅")
