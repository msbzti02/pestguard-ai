"""
PestGuard AI — Integration Test Suite (#16)

Automated end-to-end tests covering all use cases with edge cases.
Run: pytest tests/test_integration.py -v
"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ============================================================================
# UC-1: System Status
# ============================================================================
class TestSystemStatus:
    def test_root_online(self):
        r = client.get("/")
        assert r.status_code == 200
        assert r.json()["status"] == "online"

    def test_health_endpoint(self):
        r = client.get("/health")
        assert r.status_code == 200


# ============================================================================
# UC-2: Chat / AI Advisor
# ============================================================================
class TestChatbot:
    def test_chat_basic(self):
        r = client.post("/chat", json={
            "message": "What is IPM?", "session_id": "test-chat-1"
        })
        assert r.status_code == 200
        assert "reply" in r.json()
        assert len(r.json()["reply"]) > 10

    def test_chat_with_pest_context(self):
        r = client.post("/chat", json={
            "message": "How to treat?", "session_id": "test-chat-2",
            "pest_name": "Fall Armyworm", "confidence": 0.85
        })
        assert r.status_code == 200

    def test_chat_empty_message(self):
        r = client.post("/chat", json={"message": "", "session_id": "test-chat-3"})
        assert r.status_code in [400, 422]

    def test_chat_analytics(self):
        r = client.get("/chat/analytics")
        assert r.status_code == 200


# ============================================================================
# UC-3: Weather / Spray Safety
# ============================================================================
class TestWeather:
    def test_weather_valid_coords(self):
        r = client.get("/weather/39.0/35.0")
        assert r.status_code == 200
        data = r.json()
        assert "temperature" in data
        assert "safe_to_spray" in data

    def test_weather_invalid_coords(self):
        r = client.get("/weather/999/999")
        assert r.status_code in [200, 400, 422]

    def test_weather_forecast(self):
        r = client.get("/weather/forecast/39.0/35.0")
        assert r.status_code == 200
        assert "forecast" in r.json()


# ============================================================================
# UC-4: Heatmap
# ============================================================================
class TestHeatmap:
    def test_heatmap_get(self):
        r = client.get("/heatmap")
        assert r.status_code == 200

    def test_heatmap_report(self):
        r = client.post("/heatmap/report", json={
            "pest_type": "Fall Armyworm",
            "lat": 39.0, "lon": 35.0,
            "severity": "high", "crop": "Corn",
            "notes": "Test report"
        })
        assert r.status_code == 200


# ============================================================================
# UC-5: Pest Library / Knowledge
# ============================================================================
class TestPestLibrary:
    def test_pest_library(self):
        r = client.get("/pest-library")
        assert r.status_code == 200
        data = r.json()
        assert "pests" in data
        assert len(data["pests"]) > 0

    def test_pest_info(self):
        r = client.get("/pest-info/Fall Armyworm")
        assert r.status_code == 200

    def test_pest_info_unknown(self):
        r = client.get("/pest-info/UnknownPest123")
        assert r.status_code == 404


# ============================================================================
# Feature 7: Risk Score Engine
# ============================================================================
class TestRiskScore:
    def test_risk_score_basic(self):
        r = client.post("/risk-score", json={
            "pest_name": "Fall Armyworm", "lat": 39.0, "lon": 35.0,
            "confidence": 0.85
        })
        assert r.status_code == 200
        data = r.json()
        assert 0 <= data["risk_score"] <= 100
        assert data["level"] in ["Critical", "High", "Moderate", "Low", "Minimal"]
        assert "factors" in data
        assert "weather" in data

    def test_risk_score_low_threat(self):
        r = client.post("/risk-score", json={
            "pest_name": "Beet Fly", "confidence": 0.3
        })
        assert r.status_code == 200
        assert r.json()["risk_score"] < 80

    def test_risk_score_unknown_pest(self):
        r = client.post("/risk-score", json={
            "pest_name": "Unknown Pest", "confidence": 0.5
        })
        assert r.status_code == 200  # Uses default severity


# ============================================================================
# Feature 8: Treatment Timeline Tracker
# ============================================================================
class TestTreatmentTracker:
    def test_start_treatment(self):
        r = client.post("/treatment/start", json={
            "pest_name": "Fall Armyworm", "crop": "Corn",
            "session_id": "test-session-1", "field_size_ha": 5.0
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "active"
        assert len(data["steps"]) > 0
        assert data["progress"] == 0
        return data["plan_id"]

    def test_complete_step(self):
        # Start a plan first
        r1 = client.post("/treatment/start", json={
            "pest_name": "Fall Armyworm", "crop": "Corn",
            "session_id": "test-session-2", "field_size_ha": 1.0
        })
        plan_id = r1.json()["plan_id"]
        # Complete step 0
        r2 = client.post(f"/treatment/{plan_id}/complete/0")
        assert r2.status_code == 200
        assert r2.json()["progress"] > 0

    def test_get_active_plans(self):
        r = client.get("/treatment/active/test-session-1")
        assert r.status_code == 200
        assert "plans" in r.json()

    def test_invalid_plan(self):
        r = client.get("/treatment/nonexistent-plan")
        assert r.status_code == 404


# ============================================================================
# Feature 9: Historical Trends
# ============================================================================
class TestHistoricalTrends:
    def test_trends_empty(self):
        r = client.get("/trends?days=1")
        assert r.status_code == 200

    def test_trends_default(self):
        r = client.get("/trends")
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        assert "top_pests" in data


# ============================================================================
# Feature 10: Regional Alerts
# ============================================================================
class TestRegionalAlerts:
    def test_alerts_endpoint(self):
        r = client.get("/alerts")
        assert r.status_code == 200
        assert "alerts" in r.json()

    def test_alerts_with_threshold(self):
        r = client.get("/alerts?threshold=100")
        assert r.status_code == 200
        assert r.json()["total"] == 0  # High threshold = no alerts


# ============================================================================
# UC-6: Economic Impact Calculator
# ============================================================================
class TestEconomicImpact:
    def test_economic_impact(self):
        r = client.post("/economic-impact", json={
            "pest_name": "Fall Armyworm", "crop": "Corn",
            "field_size_ha": 5.0, "infestation_level": "severe"
        })
        assert r.status_code == 200
        data = r.json()
        assert data["urgency"] in ["EMERGENCY", "HIGH", "MODERATE", "LOW"]
        assert data["yield_impact"]["potential_loss_usd"] > 0

    def test_economic_with_stage(self):
        r = client.post("/economic-impact", json={
            "pest_name": "Fall Armyworm", "crop": "Corn",
            "field_size_ha": 1.0, "infestation_level": "light",
            "growth_stage": "seedling"
        })
        assert r.status_code == 200

    def test_crop_stages(self):
        r = client.get("/crop-stages/Corn")
        assert r.status_code == 200
        assert len(r.json()["stages"]) > 0

    def test_crop_list(self):
        r = client.get("/economic-impact/crops")
        assert r.status_code == 200


# ============================================================================
# UC-7: Feedback Loop
# ============================================================================
class TestFeedbackLoop:
    def test_submit_correct_feedback(self):
        r = client.post("/feedback", json={
            "session_id": "test-fb-1",
            "prediction_pest": "Fall Armyworm",
            "confidence": 0.85,
            "is_correct": True
        })
        assert r.status_code == 200
        assert r.json()["status"] == "received"

    def test_submit_correction(self):
        r = client.post("/feedback", json={
            "session_id": "test-fb-2",
            "prediction_pest": "Corn Borer",
            "confidence": 0.72,
            "is_correct": False,
            "actual_pest": "Fall Armyworm"
        })
        assert r.status_code == 200

    def test_feedback_analytics(self):
        r = client.get("/feedback/analytics")
        assert r.status_code == 200
        data = r.json()
        assert "total_feedback" in data
        assert "accuracy_rate" in data


# ============================================================================
# Feature 14: Pest Lifecycle
# ============================================================================
class TestPestLifecycle:
    def test_known_pest(self):
        r = client.get("/pest-lifecycle/Fall Armyworm")
        assert r.status_code == 200
        data = r.json()
        assert len(data["stages"]) >= 3
        assert "total_cycle_days" in data
        assert data["stages"][0]["name"] == "Egg"

    def test_unknown_pest_default(self):
        r = client.get("/pest-lifecycle/Unknown Bug")
        assert r.status_code == 200
        assert len(r.json()["stages"]) >= 3


# ============================================================================
# Feature 15: Farmer Fields
# ============================================================================
class TestFarmerFields:
    def test_save_field(self):
        r = client.post("/fields", json={
            "name": "Test Wheat Field", "lat": 39.5, "lon": 32.8,
            "crop": "Wheat", "area_ha": 15.0
        })
        assert r.status_code == 200
        assert r.json()["name"] == "Test Wheat Field"

    def test_get_fields(self):
        r = client.get("/fields")
        assert r.status_code == 200
        assert "fields" in r.json()

    def test_delete_field(self):
        # Save first
        r1 = client.post("/fields", json={
            "name": "To Delete", "lat": 40.0, "lon": 33.0,
            "crop": "Corn", "area_ha": 2.0
        })
        fid = r1.json()["id"]
        r2 = client.delete(f"/fields/{fid}")
        assert r2.status_code == 200


# ============================================================================
# Edge Cases & Error Handling
# ============================================================================
class TestEdgeCases:
    def test_nonexistent_endpoint(self):
        r = client.get("/api/nonexistent/path")
        assert r.status_code == 404

    def test_wrong_method(self):
        r = client.get("/risk-score")
        assert r.status_code in [405, 422]

    def test_invalid_json(self):
        r = client.post("/risk-score", content="not json",
                       headers={"Content-Type": "application/json"})
        assert r.status_code == 422

    def test_missing_required_fields(self):
        r = client.post("/economic-impact", json={"pest_name": "Fall Armyworm"})
        assert r.status_code == 422

    def test_frontend_serves(self):
        r = client.get("/app")
        assert r.status_code == 200
        assert "PestGuard" in r.text
