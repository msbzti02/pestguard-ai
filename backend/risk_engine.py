"""
PestGuard AI — Risk Score Engine, Regional Alerts & Historical Trends

Features:
  ✅ #7  Pest Risk Score (0-100) combining weather+region+season+severity
  ✅ #9  Historical trend tracking for predictions over time
  ✅ #10 Regional outbreak alert generation
  ✅ #14 Pest lifecycle stage data
"""

from datetime import datetime, timedelta
from collections import Counter
import math, hashlib

# ============================================================================
# SEASONAL RISK FACTORS (Northern Hemisphere / Turkey)
# ============================================================================
SEASON_RISK = {
    1: 0.15, 2: 0.20, 3: 0.45, 4: 0.65, 5: 0.80, 6: 0.95,
    7: 1.00, 8: 0.95, 9: 0.75, 10: 0.50, 11: 0.30, 12: 0.15,
}

PEST_BASE_SEVERITY = {
    "Rice Leaf Roller": 55, "Rice Leaf Caterpillar": 60,
    "Paddy Stem Maggot": 50, "Asiatic Rice Borer": 72,
    "Yellow Rice Borer": 75, "Brown Planthopper": 85,
    "Rice Leafhopper": 65, "Green Peach Aphid": 45,
    "Beet Fly": 35, "Beet Armyworm": 68,
    "Corn Borer": 62, "Fall Armyworm": 82,
    "Wheat Aphid": 42, "Wheat Midge": 48,
    "Peach Borer": 55, "Cabbage Looper": 50,
    "Diamondback Moth": 72, "Cotton Bollworm": 78,
    "Citrus Leaf Miner": 38, "Whitefly": 58,
    "Thrips": 44, "Colorado Potato Beetle": 76,
    "Migratory Locust": 95, "Red Spider Mite": 40,
    "Mole Cricket": 42, "Stink Bug": 46,
    "Spotted Lanternfly": 60, "Aphid": 48,
}

# ============================================================================
# PEST LIFECYCLE DATA (#14)
# ============================================================================
PEST_LIFECYCLE = {
    "Fall Armyworm": {
        "stages": [
            {"name": "Egg", "icon": "🥚", "duration": "3-5 days", "days": 4,
             "description": "Eggs laid in clusters of 100-200 on leaf surfaces, covered with moth scales",
             "vulnerability": "High", "best_control": "Destroy egg masses manually, release Trichogramma wasps",
             "conditions": "Optimal at 25-28°C, 70-90% humidity"},
            {"name": "Larva", "icon": "🐛", "duration": "14-21 days", "days": 18,
             "description": "Six instars, feeds voraciously on whorl leaves. Most destructive stage",
             "vulnerability": "Medium", "best_control": "Bt sprays (Bacillus thuringiensis), Spinosad, Neem oil",
             "conditions": "Active feeders at 20-30°C, hide in whorls during day"},
            {"name": "Pupa", "icon": "🫘", "duration": "7-13 days", "days": 10,
             "description": "Pupation occurs 2-8 cm deep in soil near host plant base",
             "vulnerability": "Low", "best_control": "Deep plowing to expose pupae, soil-applied insecticides",
             "conditions": "Soil temperature 15-30°C, moisture-dependent"},
            {"name": "Adult Moth", "icon": "🦋", "duration": "10-21 days", "days": 15,
             "description": "Nocturnal moths, strong fliers capable of migrating 100+ km per night",
             "vulnerability": "Low", "best_control": "Pheromone traps for monitoring, light traps",
             "conditions": "Most active at night, 20-30°C optimal flight"},
        ],
        "total_cycle_days": 47, "generations_per_year": "4-6",
        "critical_window": "Early larval stages (1st-3rd instar) — apply Bt within first 7 days of hatching",
    },
    "Rice Leafhopper": {
        "stages": [
            {"name": "Egg", "icon": "🥚", "duration": "6-9 days", "days": 7,
             "description": "Inserted into leaf midrib or sheath tissue in rows",
             "vulnerability": "High", "best_control": "Resistant varieties, remove alternate hosts",
             "conditions": "25-30°C optimal, high humidity accelerates hatching"},
            {"name": "Nymph", "icon": "🐛", "duration": "15-20 days", "days": 17,
             "description": "Five nymphal instars, wingless, feeds on phloem sap. Transmits tungro virus",
             "vulnerability": "High", "best_control": "Imidacloprid seed treatment, neem-based sprays",
             "conditions": "Thrives in dense canopy with high nitrogen"},
            {"name": "Adult", "icon": "🦗", "duration": "20-30 days", "days": 25,
             "description": "Winged adults, strong vector for Rice Tungro Disease. Attracted to light",
             "vulnerability": "Medium", "best_control": "Light traps, avoid excessive nitrogen, predator conservation",
             "conditions": "Peak activity at dusk, 25-30°C"},
        ],
        "total_cycle_days": 49, "generations_per_year": "5-7",
        "critical_window": "Nymph stage — economic threshold is 5-10 per hill",
    },
    "Brown Planthopper": {
        "stages": [
            {"name": "Egg", "icon": "🥚", "duration": "5-8 days", "days": 6,
             "description": "Laid inside leaf sheath, 2-12 eggs per cluster",
             "vulnerability": "High", "best_control": "Flood field briefly, remove egg-bearing tillers",
             "conditions": "26-29°C, >80% RH"},
            {"name": "Nymph", "icon": "🐛", "duration": "12-17 days", "days": 15,
             "description": "Five instars, phloem feeder causing 'hopper burn'. Excretes honeydew",
             "vulnerability": "High", "best_control": "Alternate wetting-drying, Buprofezin, spider conservation",
             "conditions": "Dense plant spacing + high nitrogen = outbreak"},
            {"name": "Adult", "icon": "🦗", "duration": "10-20 days", "days": 15,
             "description": "Macropterous (long-winged) or brachypterous forms. Mass migration events",
             "vulnerability": "Medium", "best_control": "Light traps, avoid broad-spectrum insecticides",
             "conditions": "Outbreaks after resurgence from insecticide overuse"},
        ],
        "total_cycle_days": 36, "generations_per_year": "6-8",
        "critical_window": "Nymph at tillering stage — threshold 10-15 per hill",
    },
    "Corn Borer": {
        "stages": [
            {"name": "Egg", "icon": "🥚", "duration": "4-7 days", "days": 5,
             "description": "Flat, overlapping egg masses on underside of leaves near midrib",
             "vulnerability": "High", "best_control": "Trichogramma releases, hand removal of egg masses",
             "conditions": "20-28°C, moderate humidity"},
            {"name": "Larva", "icon": "🐛", "duration": "20-30 days", "days": 25,
             "description": "Bores into stalks causing structural weakness and yield loss. 5 instars",
             "vulnerability": "Medium (early) / Low (inside stalk)", "best_control": "Bt corn, granular insecticides in whorl before boring",
             "conditions": "Must treat before larvae enter stalk (first 5-7 days)"},
            {"name": "Pupa", "icon": "🫘", "duration": "10-14 days", "days": 12,
             "description": "Pupation inside stalk tunnels or in soil debris",
             "vulnerability": "Low", "best_control": "Stalk destruction after harvest, deep plowing",
             "conditions": "Overwinters as mature larva in stalks"},
            {"name": "Adult Moth", "icon": "🦋", "duration": "7-14 days", "days": 10,
             "description": "Nocturnal, attracted to light. Females lay 15-35 egg masses",
             "vulnerability": "Low", "best_control": "Blacklight traps for population monitoring",
             "conditions": "Peak emergence at dusk, 24-30°C"},
        ],
        "total_cycle_days": 52, "generations_per_year": "2-3",
        "critical_window": "First 5 days after larval hatch — before they bore into stalks",
    },
    "Cotton Bollworm": {
        "stages": [
            {"name": "Egg", "icon": "🥚", "duration": "3-5 days", "days": 4,
             "description": "Single eggs on tender plant parts (flowers, young bolls, leaf hairs)",
             "vulnerability": "High", "best_control": "Egg parasitoids (Trichogramma), scouting twice weekly",
             "conditions": "25-28°C, flowering stage of cotton"},
            {"name": "Larva", "icon": "🐛", "duration": "14-20 days", "days": 17,
             "description": "Feeds on squares, flowers, and bolls. Color varies green to brown. 6 instars",
             "vulnerability": "Medium", "best_control": "NPV (nuclear polyhedrosis virus), Spinosad, hand-picking",
             "conditions": "Most damaging at boll formation, feeds inside bolls"},
            {"name": "Pupa", "icon": "🫘", "duration": "10-15 days", "days": 12,
             "description": "Pupates in soil at 5-10 cm depth. Can enter diapause in winter",
             "vulnerability": "Low", "best_control": "Post-harvest deep plowing, flood irrigation",
             "conditions": "Soil temperature >15°C for development"},
            {"name": "Adult Moth", "icon": "🦋", "duration": "10-25 days", "days": 17,
             "description": "Strong nocturnal flier, highly polyphagous (200+ host plants)",
             "vulnerability": "Low", "best_control": "Pheromone traps (Z-11-hexadecenal), crop rotation",
             "conditions": "Peak flight 2-4 hours after sunset"},
        ],
        "total_cycle_days": 50, "generations_per_year": "3-5",
        "critical_window": "Early larval stage on squares/flowers — before boll entry",
    },
}

# Default lifecycle for pests without specific data
DEFAULT_LIFECYCLE = {
    "stages": [
        {"name": "Egg", "icon": "🥚", "duration": "3-7 days", "days": 5,
         "description": "Eggs deposited on host plant tissue",
         "vulnerability": "High", "best_control": "Destroy egg masses, biological control agents",
         "conditions": "Warm, humid conditions accelerate development"},
        {"name": "Larva/Nymph", "icon": "🐛", "duration": "14-28 days", "days": 21,
         "description": "Active feeding stage causing primary crop damage",
         "vulnerability": "Medium", "best_control": "Targeted insecticides, biological controls, IPM",
         "conditions": "Most active in warm weather with adequate food supply"},
        {"name": "Pupa/Pre-adult", "icon": "🫘", "duration": "7-14 days", "days": 10,
         "description": "Transformation stage, typically in soil or sheltered location",
         "vulnerability": "Low", "best_control": "Cultural practices (plowing, crop rotation)",
         "conditions": "Protected stage, difficult to reach with treatments"},
        {"name": "Adult", "icon": "🦋", "duration": "14-30 days", "days": 22,
         "description": "Reproductive stage, dispersal and egg-laying",
         "vulnerability": "Low", "best_control": "Traps (pheromone/light), habitat management",
         "conditions": "Most active during warm evenings and nights"},
    ],
    "total_cycle_days": 58, "generations_per_year": "3-5",
    "critical_window": "Early larval/nymph stage — first 7 days after hatching",
}


def calculate_risk_score(
    pest_name: str,
    temperature: float = 25.0,
    humidity: float = 60.0,
    wind_speed: float = 10.0,
    rain_probability: float = 20.0,
    nearby_reports: int = 0,
    month: int = None,
    confidence: float = 0.8,
) -> dict:
    """Calculate 0-100 pest risk score from multiple factors."""
    if month is None:
        month = datetime.now().month

    # Factor 1: Pest base severity (30%)
    base = PEST_BASE_SEVERITY.get(pest_name, 50)
    severity_score = base

    # Factor 2: Weather conditions (25%)
    temp_risk = 0
    if 22 <= temperature <= 32:
        temp_risk = 80 + (10 - abs(temperature - 27)) * 2
    elif 15 <= temperature < 22:
        temp_risk = 40 + (temperature - 15) * 5.7
    elif temperature > 32:
        temp_risk = max(20, 100 - (temperature - 32) * 8)
    else:
        temp_risk = max(10, temperature * 2.5)

    humidity_risk = min(100, humidity * 1.2) if humidity > 50 else humidity
    wind_risk = max(0, 100 - wind_speed * 4) if wind_speed > 15 else 70 + wind_speed
    rain_risk = min(100, rain_probability * 1.5)
    weather_score = (temp_risk * 0.35 + humidity_risk * 0.30 + wind_risk * 0.15 + rain_risk * 0.20)

    # Factor 3: Seasonal risk (20%)
    season_score = SEASON_RISK.get(month, 0.5) * 100

    # Factor 4: Regional activity (15%)
    region_score = min(100, nearby_reports * 8) if nearby_reports > 0 else 10

    # Factor 5: Detection confidence (10%)
    conf_score = confidence * 100

    # Weighted combination
    risk = (
        severity_score * 0.30 +
        weather_score * 0.25 +
        season_score * 0.20 +
        region_score * 0.15 +
        conf_score * 0.10
    )
    risk = max(0, min(100, round(risk, 1)))

    # Risk level
    if risk >= 80:
        level, color, action = "Critical", "#dc2626", "Immediate intervention required"
    elif risk >= 60:
        level, color, action = "High", "#ef4444", "Urgent treatment recommended"
    elif risk >= 40:
        level, color, action = "Moderate", "#f59e0b", "Monitor closely, prepare controls"
    elif risk >= 20:
        level, color, action = "Low", "#22c55e", "Routine monitoring sufficient"
    else:
        level, color, action = "Minimal", "#10b981", "No action needed"

    return {
        "risk_score": risk,
        "level": level,
        "color": color,
        "action": action,
        "factors": {
            "pest_severity": {"score": round(severity_score, 1), "weight": "30%"},
            "weather": {"score": round(weather_score, 1), "weight": "25%",
                       "details": {"temp": round(temp_risk,1), "humidity": round(humidity_risk,1),
                                   "wind": round(wind_risk,1), "rain": round(rain_risk,1)}},
            "season": {"score": round(season_score, 1), "weight": "20%", "month": month},
            "region": {"score": round(region_score, 1), "weight": "15%", "nearby_reports": nearby_reports},
            "confidence": {"score": round(conf_score, 1), "weight": "10%"},
        },
    }


# ============================================================================
# HISTORICAL TRENDS (#9)
# ============================================================================
_prediction_history: list = []

def record_prediction(pest_name: str, confidence: float, crop: str, timestamp: str = None):
    """Record a prediction for trend analysis."""
    _prediction_history.append({
        "pest_name": pest_name,
        "confidence": confidence,
        "crop": crop,
        "timestamp": timestamp or datetime.now().isoformat(),
    })
    if len(_prediction_history) > 2000:
        _prediction_history.pop(0)

def get_trend_data(days: int = 30) -> dict:
    """Get pest detection trends over the specified period."""
    cutoff = datetime.now() - timedelta(days=days)
    recent = [p for p in _prediction_history
              if datetime.fromisoformat(p["timestamp"]) > cutoff]

    if not recent:
        return {"total": 0, "period_days": days, "trends": [], "top_pests": [],
                "daily_counts": [], "crop_distribution": {}, "message": "No data yet"}

    pest_counts = Counter(p["pest_name"] for p in recent)
    crop_counts = Counter(p["crop"] for p in recent)
    top_pests = [{"pest": k, "count": v, "pct": round(v/len(recent)*100,1)}
                 for k, v in pest_counts.most_common(10)]

    # Daily counts for chart
    daily = {}
    for p in recent:
        day = p["timestamp"][:10]
        daily[day] = daily.get(day, 0) + 1
    daily_list = [{"date": k, "count": v} for k, v in sorted(daily.items())]

    # Trend direction (compare last 7 days vs previous 7 days)
    now = datetime.now()
    last_week = [p for p in recent if datetime.fromisoformat(p["timestamp"]) > now - timedelta(days=7)]
    prev_week = [p for p in recent if now - timedelta(days=14) < datetime.fromisoformat(p["timestamp"]) <= now - timedelta(days=7)]
    trend_dir = "rising" if len(last_week) > len(prev_week) * 1.2 else \
                "falling" if len(last_week) < len(prev_week) * 0.8 else "stable"

    # Per-pest trends
    pest_trends = []
    for pest, count in pest_counts.most_common(5):
        lw = sum(1 for p in last_week if p["pest_name"] == pest)
        pw = sum(1 for p in prev_week if p["pest_name"] == pest)
        change = round((lw - pw) / max(pw, 1) * 100, 1)
        pest_trends.append({"pest": pest, "this_week": lw, "last_week": pw,
                           "change_pct": change, "direction": "↑" if change > 10 else "↓" if change < -10 else "→"})

    return {
        "total": len(recent), "period_days": days,
        "overall_trend": trend_dir,
        "top_pests": top_pests,
        "pest_trends": pest_trends,
        "daily_counts": daily_list,
        "crop_distribution": dict(crop_counts),
        "avg_confidence": round(sum(p["confidence"] for p in recent) / len(recent), 3),
    }


# ============================================================================
# REGIONAL ALERTS (#10)
# ============================================================================
def check_outbreak_alerts(heatmap_data: list, threshold: int = 8) -> list:
    """Analyze heatmap data for outbreak conditions."""
    alerts = []
    region_data = {}
    for point in heatmap_data:
        key = f"{point.get('pest_type','Unknown')}_{round(point.get('grid_lat',0))}"
        if key not in region_data:
            region_data[key] = {"pest": point.get("pest_type","Unknown"),
                               "lat": point.get("grid_lat",0), "lon": point.get("grid_lon",0),
                               "total": 0, "points": []}
        region_data[key]["total"] += point.get("count", 1)
        region_data[key]["points"].append(point)

    for key, data in region_data.items():
        if data["total"] >= threshold:
            severity = "Critical" if data["total"] >= threshold * 3 else \
                       "High" if data["total"] >= threshold * 2 else "Elevated"
            color = "#dc2626" if severity == "Critical" else "#ef4444" if severity == "High" else "#f59e0b"
            alerts.append({
                "pest": data["pest"], "severity": severity, "color": color,
                "total_reports": data["total"],
                "center_lat": data["lat"], "center_lon": data["lon"],
                "message": f"🚨 {severity} outbreak: {data['pest']} — {data['total']} reports detected",
                "recommendation": "Immediate field scouting and regional IPM coordination recommended"
                                  if severity == "Critical" else "Enhanced monitoring and preventive measures advised",
            })

    return sorted(alerts, key=lambda a: -a["total_reports"])


def get_pest_lifecycle(pest_name: str) -> dict:
    """Get lifecycle data for a pest."""
    data = PEST_LIFECYCLE.get(pest_name, DEFAULT_LIFECYCLE)
    return {"pest_name": pest_name, **data}
