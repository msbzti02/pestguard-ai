"""Quick weather test."""
import httpx

r = httpx.get("http://localhost:8000/weather/41.0/29.0", timeout=10)
w = r.json()

print("=" * 50)
print("REAL WEATHER DATA — Istanbul")
print("=" * 50)
for key in ["temperature", "humidity", "wind_speed", "rain_probability", "condition", "safe_to_spray", "alerts", "is_mock", "disclaimer"]:
    val = w.get(key, "N/A")
    print(f"  {key}: {val}")
print("=" * 50)
