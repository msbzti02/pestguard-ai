"""
Mock API Layer — Simulates Department 3 (Model) and Department 1 (XAI) outputs.

PURPOSE:
    This file provides fake/hardcoded responses that mimic what the real ML model
    and Grad-CAM system will return. This lets Department 2 build and test EVERYTHING
    without waiting for other departments.

WHEN TO REPLACE:
    When D3 delivers their trained model API → replace get_prediction() internals
    When D1 delivers their Grad-CAM API → replace get_gradcam() internals
    The function signatures stay the same — only the inside changes.
"""

import random
from datetime import datetime


# ============================================================================
# IP102 Dataset — Sample pest names for realistic mock data
# These are real pest categories from the IP102 dataset
# ============================================================================
MOCK_PEST_DATABASE = [
    {"category_id": 0, "pest_name": "Rice Leaf Roller", "crop": "Rice"},
    {"category_id": 1, "pest_name": "Rice Leaf Caterpillar", "crop": "Rice"},
    {"category_id": 2, "pest_name": "Paddy Stem Maggot", "crop": "Rice"},
    {"category_id": 3, "pest_name": "Asiatic Rice Borer", "crop": "Rice"},
    {"category_id": 4, "pest_name": "Yellow Rice Borer", "crop": "Rice"},
    {"category_id": 14, "pest_name": "Aphid", "crop": "Multiple"},
    {"category_id": 15, "pest_name": "Beet Fly", "crop": "Beet"},
    {"category_id": 24, "pest_name": "Corn Borer", "crop": "Corn"},
    {"category_id": 37, "pest_name": "Wheat Aphid", "crop": "Wheat"},
    {"category_id": 50, "pest_name": "Peach Borer", "crop": "Peach"},
    {"category_id": 72, "pest_name": "Citrus Leaf Miner", "crop": "Citrus"},
    {"category_id": 88, "pest_name": "Locust", "crop": "Multiple"},
    {"category_id": 95, "pest_name": "Mole Cricket", "crop": "Multiple"},
    {"category_id": 101, "pest_name": "Lycorma Delicatula", "crop": "Multiple"},
]


def get_prediction(image_path: str = None, simulate_low_confidence: bool = False) -> dict:
    """
    Simulates Department 3's pest classification model output.

    In the REAL system, this will:
        - Send the image to D3's inference API
        - Receive the predicted pest class + confidence score

    For now, returns realistic mock data.

    Args:
        image_path: Path to the uploaded image (unused in mock, needed for real API)
        simulate_low_confidence: If True, returns a low-confidence result for testing

    Returns:
        dict with keys: pest_name, confidence, category_id, crop, timestamp
    """
    if simulate_low_confidence:
        return {
            "pest_name": "Uncertain",
            "confidence": round(random.uniform(0.20, 0.65), 2),
            "category_id": -1,
            "crop": "Unknown",
            "timestamp": datetime.now().isoformat(),
            "is_mock": True
        }

    # Pick a random pest from our database for realistic variety
    pest = random.choice(MOCK_PEST_DATABASE)
    return {
        "pest_name": pest["pest_name"],
        "confidence": round(random.uniform(0.72, 0.98), 2),
        "category_id": pest["category_id"],
        "crop": pest["crop"],
        "timestamp": datetime.now().isoformat(),
        "is_mock": True
    }


def get_gradcam(image_path: str = None) -> dict:
    """
    Simulates Department 1's Grad-CAM XAI visualization output.

    In the REAL system, this will:
        - Send the image to D1's Grad-CAM API
        - Receive a heatmap overlay image URL showing which parts of the
          image the model focused on

    For now, returns a placeholder path.

    Args:
        image_path: Path to the uploaded image

    Returns:
        dict with keys: heatmap_url, method, explanation
    """
    return {
        "heatmap_url": "/static/mock_gradcam_heatmap.png",
        "method": "Grad-CAM",
        "explanation": "This heatmap shows which regions of the image the model "
                       "focused on when making its prediction. Brighter areas "
                       "indicate higher importance.",
        "is_mock": True
    }


def get_vlm_description(image_path: str = None) -> dict:
    """
    Simulates VLM (Vision-Language Model) image description.

    In the REAL system (Stage 3), BLIP-2 or LLaVA will generate this.
    For now, returns a hardcoded description.

    Args:
        image_path: Path to the uploaded image

    Returns:
        dict with keys: description, model_used
    """
    mock_descriptions = [
        "A small green insect with translucent wings resting on a rice leaf. "
        "The leaf shows minor yellowing damage around the insect's position.",

        "A brown caterpillar-like larva on the stem of a cereal plant. "
        "Visible feeding damage on the stem surface.",

        "A cluster of tiny aphids on the underside of a broad green leaf. "
        "Some honeydew residue visible on the leaf surface.",

        "A winged beetle with dark brown coloring sitting on a corn stalk. "
        "The surrounding leaves show small bore holes.",
    ]
    return {
        "description": random.choice(mock_descriptions),
        "model_used": "mock (BLIP-2 placeholder)",
        "is_mock": True
    }


# ============================================================================
# Mock weather data (used before real weather API is connected in Stage 3)
# ============================================================================
def get_mock_weather(lat: float = 41.0, lon: float = 29.0) -> dict:
    """
    Simulates weather API response.
    Will be replaced by real OpenWeatherMap / MGM calls in Stage 3.
    """
    scenarios = [
        {
            "temperature": 22, "humidity": 55, "wind_speed": 8,
            "rain_probability": 10, "condition": "Clear",
            "alerts": [], "safe_to_spray": True,
        },
        {
            "temperature": 18, "humidity": 85, "wind_speed": 25,
            "rain_probability": 80, "condition": "Heavy Rain",
            "alerts": ["Heavy rainfall warning"],
            "safe_to_spray": False,
        },
        {
            "temperature": 5, "humidity": 70, "wind_speed": 40,
            "rain_probability": 60, "condition": "Storm",
            "alerts": ["Strong wind warning", "Hail risk"],
            "safe_to_spray": False,
        },
    ]
    weather = random.choice(scenarios)
    weather.update({
        "lat": lat, "lon": lon,
        "timestamp": datetime.now().isoformat(),
        "is_mock": True,
        "disclaimer": (
            "⚠️ Weather data reflects broad regional forecasts. "
            "Actual field conditions (fog, local frost) may differ. "
            "Always verify conditions on-site before spraying."
        )
    })
    return weather


# ============================================================================
# Mock heatmap data
# ============================================================================
def get_mock_heatmap_data() -> list:
    """
    Returns synthetic pest outbreak data points for the heatmap.
    Coordinates are rounded to 0.1° grid (~11km) for anonymization.
    """
    return [
        {"grid_lat": 41.0, "grid_lon": 29.0, "pest_type": "Aphid", "count": 15, "region": "Istanbul"},
        {"grid_lat": 39.9, "grid_lon": 32.9, "pest_type": "Wheat Aphid", "count": 22, "region": "Ankara"},
        {"grid_lat": 38.4, "grid_lon": 27.1, "pest_type": "Citrus Leaf Miner", "count": 8, "region": "Izmir"},
        {"grid_lat": 37.0, "grid_lon": 35.3, "pest_type": "Corn Borer", "count": 18, "region": "Adana"},
        {"grid_lat": 40.2, "grid_lon": 29.0, "pest_type": "Rice Leaf Roller", "count": 30, "region": "Bursa"},
        {"grid_lat": 36.9, "grid_lon": 30.7, "pest_type": "Locust", "count": 5, "region": "Antalya"},
        {"grid_lat": 41.3, "grid_lon": 36.3, "pest_type": "Beet Fly", "count": 11, "region": "Samsun"},
        {"grid_lat": 39.7, "grid_lon": 30.5, "pest_type": "Mole Cricket", "count": 7, "region": "Eskisehir"},
        {"grid_lat": 37.8, "grid_lon": 32.5, "pest_type": "Aphid", "count": 14, "region": "Konya"},
        {"grid_lat": 40.7, "grid_lon": 30.3, "pest_type": "Yellow Rice Borer", "count": 9, "region": "Sakarya"},
    ]
