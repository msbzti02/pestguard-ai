"""
Mock API Layer — Simulates Department 3 (Model) and Department 1 (XAI) outputs.

PURPOSE:
    This file provides realistic mock responses that mimic what the real ML model
    and Grad-CAM system will return. This lets Department 2 build and test EVERYTHING
    without waiting for other departments.

DESIGN:
    - Same image always returns the same prediction (deterministic via file hash)
    - Top-3 predictions with realistic confidence distributions
    - VLM descriptions matched to the predicted pest species
    - 27 pest species from the IP-102 dataset

WHEN TO REPLACE:
    When D3 delivers their trained model API → replace get_prediction() internals
    When D1 delivers their Grad-CAM API → replace get_gradcam() internals
    The function signatures stay the same — only the inside changes.
"""

import random
import hashlib
from datetime import datetime
from pathlib import Path


MOCK_PEST_DATABASE = [
    {"category_id": 0,  "pest_name": "Rice Leaf Roller",       "crop": "Rice",       "severity": "High",   "family": "Pyralidae"},
    {"category_id": 1,  "pest_name": "Rice Leaf Caterpillar",  "crop": "Rice",       "severity": "High",   "family": "Noctuidae"},
    {"category_id": 2,  "pest_name": "Paddy Stem Maggot",      "crop": "Rice",       "severity": "Medium", "family": "Chloropidae"},
    {"category_id": 3,  "pest_name": "Asiatic Rice Borer",     "crop": "Rice",       "severity": "High",   "family": "Crambidae"},
    {"category_id": 4,  "pest_name": "Yellow Rice Borer",      "crop": "Rice",       "severity": "High",   "family": "Crambidae"},
    {"category_id": 8,  "pest_name": "Brown Planthopper",      "crop": "Rice",       "severity": "High",   "family": "Delphacidae"},
    {"category_id": 12, "pest_name": "Rice Leafhopper",        "crop": "Rice",       "severity": "High",   "family": "Cicadellidae"},
    {"category_id": 14, "pest_name": "Green Peach Aphid",      "crop": "Vegetables", "severity": "Medium", "family": "Aphididae"},
    {"category_id": 15, "pest_name": "Beet Fly",               "crop": "Beet",       "severity": "Medium", "family": "Agromyzidae"},
    {"category_id": 19, "pest_name": "Beet Armyworm",          "crop": "Beet",       "severity": "High",   "family": "Noctuidae"},
    {"category_id": 24, "pest_name": "Corn Borer",             "crop": "Corn",       "severity": "High",   "family": "Crambidae"},
    {"category_id": 28, "pest_name": "Fall Armyworm",          "crop": "Corn",       "severity": "High",   "family": "Noctuidae"},
    {"category_id": 37, "pest_name": "Wheat Aphid",            "crop": "Wheat",      "severity": "Medium", "family": "Aphididae"},
    {"category_id": 42, "pest_name": "Wheat Midge",            "crop": "Wheat",      "severity": "Medium", "family": "Cecidomyiidae"},
    {"category_id": 50, "pest_name": "Peach Borer",            "crop": "Peach",      "severity": "High",   "family": "Sesiidae"},
    {"category_id": 56, "pest_name": "Cabbage Looper",         "crop": "Vegetables", "severity": "Medium", "family": "Noctuidae"},
    {"category_id": 62, "pest_name": "Diamondback Moth",       "crop": "Vegetables", "severity": "High",   "family": "Plutellidae"},
    {"category_id": 68, "pest_name": "Cotton Bollworm",        "crop": "Cotton",     "severity": "High",   "family": "Noctuidae"},
    {"category_id": 72, "pest_name": "Citrus Leaf Miner",      "crop": "Citrus",     "severity": "Medium", "family": "Gracillariidae"},
    {"category_id": 78, "pest_name": "Whitefly",               "crop": "Multiple",   "severity": "Medium", "family": "Aleyrodidae"},
    {"category_id": 82, "pest_name": "Thrips",                 "crop": "Multiple",   "severity": "Medium", "family": "Thripidae"},
    {"category_id": 85, "pest_name": "Colorado Potato Beetle",  "crop": "Potato",     "severity": "High",   "family": "Chrysomelidae"},
    {"category_id": 88, "pest_name": "Migratory Locust",       "crop": "Multiple",   "severity": "High",   "family": "Acrididae"},
    {"category_id": 92, "pest_name": "Red Spider Mite",        "crop": "Multiple",   "severity": "Medium", "family": "Tetranychidae"},
    {"category_id": 95, "pest_name": "Mole Cricket",           "crop": "Multiple",   "severity": "Medium", "family": "Gryllotalpidae"},
    {"category_id": 99, "pest_name": "Stink Bug",              "crop": "Soybean",    "severity": "Medium", "family": "Pentatomidae"},
    {"category_id": 101,"pest_name": "Spotted Lanternfly",     "crop": "Multiple",   "severity": "High",   "family": "Fulgoridae"},
]


VLM_DESCRIPTIONS = {
    "Rice Leaf Roller": "A small moth larva rolled inside a rice leaf, creating a distinctive tubular shelter. The leaf shows longitudinal folding and light green discoloration along the feeding track. Visible silk threads hold the leaf roll in place.",
    "Rice Leaf Caterpillar": "A green caterpillar with distinctive longitudinal stripes feeding on a rice leaf blade. Irregular defoliation patterns visible with ragged leaf margins. The larva is approximately 2-3 cm in length.",
    "Paddy Stem Maggot": "A small white maggot visible at the base of a rice stem near the water line. The affected tiller shows yellowing from the center outward, a classic deadheart symptom.",
    "Asiatic Rice Borer": "Bore holes visible on the rice stem with frass (insect excrement) pushed outside. The affected panicle shows whitehead symptoms — the grain head has turned white and empty.",
    "Yellow Rice Borer": "A yellowish-brown moth larva inside a split rice stem. The stem shows internal tunneling damage with brown necrotic tissue surrounding the feeding gallery.",
    "Brown Planthopper": "Clusters of small brown insects gathered at the base of rice tillers near the water surface. Characteristic 'hopper burn' pattern visible — circular patches of dried, brown plants spreading outward.",
    "Rice Leafhopper": "Small green wedge-shaped insects on the upper surface of a rice leaf. Feeding damage appears as white streaks along the leaf veins. Some honeydew deposits visible on lower leaves.",
    "Green Peach Aphid": "A dense colony of small pale green aphids clustered on the underside of a broad leaf. Honeydew residue is visible as a shiny coating on the leaf surface. Some winged adult forms present among wingless nymphs.",
    "Beet Fly": "A small dark fly with iridescent wings resting on a beet leaf. Mining damage visible as serpentine white trails on the leaf surface where larvae have fed between the epidermal layers.",
    "Beet Armyworm": "A green-brown caterpillar with a distinctive lateral stripe feeding on beet foliage. Extensive defoliation visible with only leaf veins remaining in heavily damaged areas.",
    "Corn Borer": "A pinkish-white larva boring into a corn stalk. Entry hole visible with sawdust-like frass accumulated around the bore site. The surrounding stalk tissue shows brown discoloration.",
    "Fall Armyworm": "A dark caterpillar with an inverted Y-shaped marking on the head capsule feeding on corn leaves. Characteristic window-pane damage pattern where the larva has consumed one leaf surface while leaving the other intact.",
    "Wheat Aphid": "Small yellowish-green aphids colonizing a wheat head during the grain-filling stage. Honeydew secretions visible on the flag leaf. Some aphids show the characteristic cornicles (tail pipes) clearly.",
    "Wheat Midge": "Tiny orange larvae visible inside a partially opened wheat floret. The affected grain shows shriveling and discoloration. Adult midges are small, delicate flies with long legs.",
    "Peach Borer": "Frass mixed with gummy sap (gummosis) visible at the base of a peach tree trunk. Larval tunneling has caused bark cracking and brown sap oozing from the affected area.",
    "Cabbage Looper": "A pale green caterpillar with distinctive looping movement on a cabbage leaf. Feeding damage shows irregular holes through the leaf blade, with dark frass pellets visible nearby.",
    "Diamondback Moth": "Small green larvae feeding on the underside of a brassica leaf, creating characteristic window-pane damage. The tiny adult moth is visible with a diamond-shaped pattern when wings are folded.",
    "Cotton Bollworm": "A large greenish-brown caterpillar boring into a cotton boll. The entry hole shows frass and damaged lint fibers. The larva has distinctive microspines and alternating light and dark body bands.",
    "Citrus Leaf Miner": "Distinctive serpentine silvery trails on a young citrus leaf caused by larval mining between leaf layers. The leaf shows curling and distortion at the margins. A small larva is visible at the end of the mine.",
    "Whitefly": "A cloud of tiny white-winged insects on the underside of a leaf. Disturbing the leaf causes them to flutter briefly before resettling. Yellow sticky residue (honeydew) and sooty mold visible on lower leaves.",
    "Thrips": "Extremely small, slender insects with fringed wings on a flower petal. Feeding damage appears as silvery-white stippling and scarring on the plant surface. Some dark fecal spots visible nearby.",
    "Colorado Potato Beetle": "A distinctive striped beetle with alternating black and yellow longitudinal stripes on its wing covers, feeding on potato foliage. Red-orange eggs visible in clusters on the leaf underside.",
    "Migratory Locust": "A large grasshopper-like insect with powerful hind legs perched on a cereal crop stem. The body shows characteristic brown-green coloring. Extensive defoliation visible in the background.",
    "Red Spider Mite": "Tiny red-brown mites visible under magnification on the underside of a leaf. Fine webbing covers affected areas. Feeding damage appears as yellow stippling that progresses to bronzing.",
    "Mole Cricket": "A large brown insect with powerful forelegs adapted for digging, found at the soil surface near damaged turf. Characteristic tunneling damage visible as raised soil ridges.",
    "Stink Bug": "A shield-shaped brown insect on a soybean pod. Characteristic feeding damage appears as dimpled, discolored spots on the pod surface where the insect has inserted its stylet.",
    "Spotted Lanternfly": "A striking insect with gray forewings spotted with black dots and bright red hindwings visible when in flight. Feeding on a tree trunk with sap weeping from wound sites.",
}


def _image_hash(image_path: str) -> int:
    """Generate a deterministic hash from image file so same image = same prediction."""
    if image_path and Path(image_path).exists():
        data = Path(image_path).read_bytes()
        return int(hashlib.md5(data).hexdigest(), 16)
    return random.randint(0, 999999)


def get_prediction(image_path: str = None, simulate_low_confidence: bool = False) -> dict:
    """
    Simulates Department 3's pest classification model output.

    DETERMINISTIC: Same image file always returns the same pest prediction.
    This makes the demo consistent and professional.

    In the REAL system, this will:
        - Send the image to D3's inference API
        - Receive the predicted pest class + confidence score

    Args:
        image_path: Path to the uploaded image
        simulate_low_confidence: If True, returns a low-confidence result

    Returns:
        dict with keys: pest_name, confidence, category_id, crop, timestamp, top_3
    """
    if simulate_low_confidence:
        h = _image_hash(image_path)
        pest = MOCK_PEST_DATABASE[h % len(MOCK_PEST_DATABASE)]
        rng = random.Random(h)
        return {
            "pest_name": pest["pest_name"],
            "confidence": round(rng.uniform(0.25, 0.55), 2),
            "category_id": pest["category_id"],
            "crop": pest["crop"],
            "severity": pest["severity"],
            "family": pest["family"],
            "timestamp": datetime.now().isoformat(),
            "is_mock": True,
            "top_3": [
                {"pest_name": pest["pest_name"], "confidence": round(rng.uniform(0.25, 0.55), 2), "crop": pest["crop"]},
                {"pest_name": MOCK_PEST_DATABASE[(h + 3) % len(MOCK_PEST_DATABASE)]["pest_name"], "confidence": round(rng.uniform(0.15, 0.30), 2), "crop": MOCK_PEST_DATABASE[(h + 3) % len(MOCK_PEST_DATABASE)]["crop"]},
                {"pest_name": MOCK_PEST_DATABASE[(h + 7) % len(MOCK_PEST_DATABASE)]["pest_name"], "confidence": round(rng.uniform(0.05, 0.15), 2), "crop": MOCK_PEST_DATABASE[(h + 7) % len(MOCK_PEST_DATABASE)]["crop"]},
            ],
        }

    h = _image_hash(image_path)
    rng = random.Random(h)

    pest_index = h % len(MOCK_PEST_DATABASE)
    pest = MOCK_PEST_DATABASE[pest_index]
    conf = round(rng.uniform(0.82, 0.97), 2)

    second_index = (pest_index + rng.randint(1, 5)) % len(MOCK_PEST_DATABASE)
    third_index = (pest_index + rng.randint(6, 12)) % len(MOCK_PEST_DATABASE)

    second_conf = round(conf * rng.uniform(0.25, 0.45), 2)
    third_conf = round(conf * rng.uniform(0.08, 0.20), 2)

    top_3 = [
        {"pest_name": pest["pest_name"], "confidence": conf, "crop": pest["crop"]},
        {"pest_name": MOCK_PEST_DATABASE[second_index]["pest_name"], "confidence": second_conf, "crop": MOCK_PEST_DATABASE[second_index]["crop"]},
        {"pest_name": MOCK_PEST_DATABASE[third_index]["pest_name"], "confidence": third_conf, "crop": MOCK_PEST_DATABASE[third_index]["crop"]},
    ]

    return {
        "pest_name": pest["pest_name"],
        "confidence": conf,
        "category_id": pest["category_id"],
        "crop": pest["crop"],
        "severity": pest["severity"],
        "family": pest["family"],
        "timestamp": datetime.now().isoformat(),
        "is_mock": True,
        "top_3": top_3,
    }


def get_gradcam(image_path: str = None) -> dict:
    """
    Simulates Department 1's Grad-CAM XAI visualization output.

    In the REAL system, this will:
        - Send the image to D1's Grad-CAM API
        - Receive a heatmap overlay image URL

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


def get_vlm_description(image_path: str = None, pest_name: str = None) -> dict:
    """
    Simulates VLM (Vision-Language Model) image description.
    Now returns pest-matched descriptions for consistency.

    Args:
        image_path: Path to the uploaded image
        pest_name: Name of the predicted pest (for matching description)

    Returns:
        dict with keys: description, model_used
    """
    if pest_name and pest_name in VLM_DESCRIPTIONS:
        description = VLM_DESCRIPTIONS[pest_name]
    else:
        h = _image_hash(image_path)
        pest_names = list(VLM_DESCRIPTIONS.keys())
        description = VLM_DESCRIPTIONS[pest_names[h % len(pest_names)]]

    return {
        "description": description,
        "model_used": "mock (BLIP-2 placeholder)",
        "is_mock": True
    }


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


def get_mock_heatmap_data() -> list:
    """
    Returns synthetic pest outbreak data points for the heatmap.
    Coordinates are rounded to 0.1° grid (~11km) for anonymization.
    """
    return [
        {"grid_lat": 41.0, "grid_lon": 29.0, "pest_type": "Green Peach Aphid", "count": 23, "region": "Istanbul", "severity": "High"},
        {"grid_lat": 39.9, "grid_lon": 32.9, "pest_type": "Wheat Aphid", "count": 31, "region": "Ankara", "severity": "High"},
        {"grid_lat": 38.4, "grid_lon": 27.1, "pest_type": "Citrus Leaf Miner", "count": 12, "region": "Izmir", "severity": "Medium"},
        {"grid_lat": 37.0, "grid_lon": 35.3, "pest_type": "Corn Borer", "count": 27, "region": "Adana", "severity": "High"},
        {"grid_lat": 40.2, "grid_lon": 29.0, "pest_type": "Rice Leaf Roller", "count": 45, "region": "Bursa", "severity": "High"},
        {"grid_lat": 36.9, "grid_lon": 30.7, "pest_type": "Migratory Locust", "count": 8, "region": "Antalya", "severity": "Medium"},
        {"grid_lat": 41.3, "grid_lon": 36.3, "pest_type": "Beet Fly", "count": 15, "region": "Samsun", "severity": "Medium"},
        {"grid_lat": 39.7, "grid_lon": 30.5, "pest_type": "Mole Cricket", "count": 9, "region": "Eskisehir", "severity": "Low"},
        {"grid_lat": 37.8, "grid_lon": 32.5, "pest_type": "Fall Armyworm", "count": 34, "region": "Konya", "severity": "High"},
        {"grid_lat": 40.7, "grid_lon": 30.3, "pest_type": "Yellow Rice Borer", "count": 18, "region": "Sakarya", "severity": "High"},
        {"grid_lat": 36.4, "grid_lon": 36.2, "pest_type": "Cotton Bollworm", "count": 21, "region": "Hatay", "severity": "High"},
        {"grid_lat": 38.7, "grid_lon": 35.5, "pest_type": "Whitefly", "count": 16, "region": "Kayseri", "severity": "Medium"},
        {"grid_lat": 40.1, "grid_lon": 26.4, "pest_type": "Brown Planthopper", "count": 28, "region": "Edirne", "severity": "High"},
        {"grid_lat": 37.2, "grid_lon": 28.4, "pest_type": "Red Spider Mite", "count": 11, "region": "Mugla", "severity": "Medium"},
        {"grid_lat": 39.1, "grid_lon": 29.5, "pest_type": "Colorado Potato Beetle", "count": 19, "region": "Kutahya", "severity": "High"},
    ]
"""
