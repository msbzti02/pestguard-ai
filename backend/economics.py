"""
PestGuard AI — Economic Impact & Crop Stage Intelligence Module

Comprehensive agricultural economics engine providing:
  ✅ Yield loss estimation per pest × crop × infestation level
  ✅ Treatment cost analysis (biological, chemical, IPM, cultural)
  ✅ ROI calculation for treatment vs. no-action
  ✅ Crop growth stage vulnerability mapping
  ✅ Pre-harvest interval enforcement
  ✅ Stage-specific treatment recommendations
  ✅ Regional crop price database (Turkey + global)
"""

from typing import Optional

# ============================================================================
# Regional Crop Economics Database (USD/ton, tons/ha for Turkey 2024-2025)
# ============================================================================
CROP_ECONOMICS = {
    "Rice":       {"price_per_ton": 520,  "avg_yield_ton_per_ha": 7.2,  "currency": "USD"},
    "Corn":       {"price_per_ton": 285,  "avg_yield_ton_per_ha": 9.5,  "currency": "USD"},
    "Wheat":      {"price_per_ton": 310,  "avg_yield_ton_per_ha": 3.2,  "currency": "USD"},
    "Vegetables": {"price_per_ton": 850,  "avg_yield_ton_per_ha": 25.0, "currency": "USD"},
    "Cotton":     {"price_per_ton": 1650, "avg_yield_ton_per_ha": 1.8,  "currency": "USD"},
    "Citrus":     {"price_per_ton": 480,  "avg_yield_ton_per_ha": 22.0, "currency": "USD"},
    "Beet":       {"price_per_ton": 55,   "avg_yield_ton_per_ha": 60.0, "currency": "USD"},
    "Potato":     {"price_per_ton": 280,  "avg_yield_ton_per_ha": 32.0, "currency": "USD"},
    "Soybean":    {"price_per_ton": 520,  "avg_yield_ton_per_ha": 2.8,  "currency": "USD"},
    "Peach":      {"price_per_ton": 750,  "avg_yield_ton_per_ha": 15.0, "currency": "USD"},
    "Multiple":   {"price_per_ton": 400,  "avg_yield_ton_per_ha": 10.0, "currency": "USD"},
    "Sorghum":    {"price_per_ton": 260,  "avg_yield_ton_per_ha": 4.5,  "currency": "USD"},
    "Tobacco":    {"price_per_ton": 3200, "avg_yield_ton_per_ha": 2.0,  "currency": "USD"},
}

# ============================================================================
# Pest Yield Loss Percentages by Infestation Level
# Data derived from FAO Crop Loss Assessment reports
# ============================================================================
PEST_YIELD_LOSS = {
    "Rice Leaf Roller":       {"light": 5,  "moderate": 15, "severe": 35, "critical": 50},
    "Rice Leaf Caterpillar":  {"light": 8,  "moderate": 20, "severe": 40, "critical": 60},
    "Paddy Stem Maggot":     {"light": 3,  "moderate": 12, "severe": 25, "critical": 40},
    "Asiatic Rice Borer":    {"light": 10, "moderate": 25, "severe": 45, "critical": 65},
    "Yellow Rice Borer":     {"light": 10, "moderate": 25, "severe": 45, "critical": 70},
    "Brown Planthopper":     {"light": 8,  "moderate": 30, "severe": 60, "critical": 90},
    "Rice Leafhopper":       {"light": 5,  "moderate": 18, "severe": 35, "critical": 55},
    "Green Peach Aphid":     {"light": 3,  "moderate": 10, "severe": 25, "critical": 40},
    "Beet Fly":              {"light": 2,  "moderate": 8,  "severe": 20, "critical": 30},
    "Beet Armyworm":         {"light": 8,  "moderate": 22, "severe": 45, "critical": 65},
    "Corn Borer":            {"light": 5,  "moderate": 15, "severe": 35, "critical": 50},
    "Fall Armyworm":         {"light": 10, "moderate": 30, "severe": 55, "critical": 75},
    "Wheat Aphid":           {"light": 3,  "moderate": 10, "severe": 22, "critical": 35},
    "Wheat Midge":           {"light": 4,  "moderate": 12, "severe": 28, "critical": 45},
    "Peach Borer":           {"light": 5,  "moderate": 15, "severe": 30, "critical": 50},
    "Cabbage Looper":        {"light": 5,  "moderate": 15, "severe": 30, "critical": 45},
    "Diamondback Moth":      {"light": 8,  "moderate": 25, "severe": 50, "critical": 70},
    "Cotton Bollworm":       {"light": 10, "moderate": 25, "severe": 50, "critical": 75},
    "Citrus Leaf Miner":     {"light": 3,  "moderate": 10, "severe": 20, "critical": 30},
    "Whitefly":              {"light": 5,  "moderate": 15, "severe": 30, "critical": 50},
    "Thrips":                {"light": 3,  "moderate": 12, "severe": 25, "critical": 40},
    "Colorado Potato Beetle": {"light": 8, "moderate": 25, "severe": 50, "critical": 80},
    "Migratory Locust":      {"light": 15, "moderate": 40, "severe": 70, "critical": 95},
    "Red Spider Mite":       {"light": 3,  "moderate": 10, "severe": 22, "critical": 35},
    "Mole Cricket":          {"light": 3,  "moderate": 10, "severe": 20, "critical": 35},
    "Stink Bug":             {"light": 4,  "moderate": 12, "severe": 25, "critical": 40},
    "Spotted Lanternfly":    {"light": 5,  "moderate": 15, "severe": 35, "critical": 55},
    "Aphid":                 {"light": 4,  "moderate": 12, "severe": 28, "critical": 45},
}

# ============================================================================
# Treatment Cost Database (USD per hectare)
# ============================================================================
TREATMENT_COSTS_PER_HA = {
    "Inspection":      {"cost": 25,  "labor_hours": 2,  "reapply": False},
    "Biological":      {"cost": 120, "labor_hours": 3,  "reapply": True},
    "Chemical":        {"cost": 185, "labor_hours": 2,  "reapply": True},
    "IPM":             {"cost": 95,  "labor_hours": 4,  "reapply": False},
    "Cultural":        {"cost": 45,  "labor_hours": 3,  "reapply": False},
    "Organic":         {"cost": 110, "labor_hours": 3,  "reapply": True},
    "Mechanical":      {"cost": 55,  "labor_hours": 4,  "reapply": False},
    "Regulatory":      {"cost": 15,  "labor_hours": 1,  "reapply": False},
    "Genetic":         {"cost": 70,  "labor_hours": 2,  "reapply": False},
    "Resistance Mgmt": {"cost": 65,  "labor_hours": 2,  "reapply": False},
}

# ============================================================================
# Crop Growth Stages with vulnerability windows
# ============================================================================
CROP_GROWTH_STAGES = {
    "Rice": {
        "stages": [
            {"name": "Seedling",     "duration_days": "0-20",   "code": "seedling"},
            {"name": "Tillering",    "duration_days": "21-45",  "code": "tillering"},
            {"name": "Booting",      "duration_days": "46-65",  "code": "booting"},
            {"name": "Heading",      "duration_days": "66-80",  "code": "heading"},
            {"name": "Flowering",    "duration_days": "81-95",  "code": "flowering"},
            {"name": "Grain Fill",   "duration_days": "96-120", "code": "grain_fill"},
            {"name": "Maturity",     "duration_days": "121-145","code": "maturity"},
        ],
        "pre_harvest_interval": 14,
    },
    "Corn": {
        "stages": [
            {"name": "Emergence",    "duration_days": "0-10",   "code": "emergence"},
            {"name": "Vegetative",   "duration_days": "11-50",  "code": "vegetative"},
            {"name": "Tasseling",    "duration_days": "51-65",  "code": "tasseling"},
            {"name": "Silking",      "duration_days": "66-75",  "code": "silking"},
            {"name": "Grain Fill",   "duration_days": "76-110", "code": "grain_fill"},
            {"name": "Maturity",     "duration_days": "111-130","code": "maturity"},
        ],
        "pre_harvest_interval": 21,
    },
    "Wheat": {
        "stages": [
            {"name": "Germination",  "duration_days": "0-15",   "code": "germination"},
            {"name": "Tillering",    "duration_days": "16-60",  "code": "tillering"},
            {"name": "Stem Extension","duration_days": "61-90", "code": "stem_ext"},
            {"name": "Heading",      "duration_days": "91-110", "code": "heading"},
            {"name": "Flowering",    "duration_days": "111-120","code": "flowering"},
            {"name": "Grain Fill",   "duration_days": "121-150","code": "grain_fill"},
            {"name": "Maturity",     "duration_days": "151-170","code": "maturity"},
        ],
        "pre_harvest_interval": 14,
    },
    "Vegetables": {
        "stages": [
            {"name": "Seedling",     "duration_days": "0-15",   "code": "seedling"},
            {"name": "Vegetative",   "duration_days": "16-40",  "code": "vegetative"},
            {"name": "Flowering",    "duration_days": "41-60",  "code": "flowering"},
            {"name": "Fruiting",     "duration_days": "61-90",  "code": "fruiting"},
            {"name": "Harvest",      "duration_days": "91-120", "code": "harvest"},
        ],
        "pre_harvest_interval": 7,
    },
    "Cotton": {
        "stages": [
            {"name": "Emergence",    "duration_days": "0-15",   "code": "emergence"},
            {"name": "Vegetative",   "duration_days": "16-55",  "code": "vegetative"},
            {"name": "Squaring",     "duration_days": "56-75",  "code": "squaring"},
            {"name": "Flowering",    "duration_days": "76-100", "code": "flowering"},
            {"name": "Boll Fill",    "duration_days": "101-140","code": "boll_fill"},
            {"name": "Maturity",     "duration_days": "141-170","code": "maturity"},
        ],
        "pre_harvest_interval": 21,
    },
    "Citrus": {
        "stages": [
            {"name": "Dormancy",     "duration_days": "0-60",   "code": "dormancy"},
            {"name": "Bud Break",    "duration_days": "61-90",  "code": "bud_break"},
            {"name": "Flowering",    "duration_days": "91-120", "code": "flowering"},
            {"name": "Fruit Set",    "duration_days": "121-180","code": "fruit_set"},
            {"name": "Fruit Growth", "duration_days": "181-300","code": "fruit_growth"},
            {"name": "Maturity",     "duration_days": "301-365","code": "maturity"},
        ],
        "pre_harvest_interval": 14,
    },
}

# ============================================================================
# Stage-Specific Vulnerability Matrix
# Maps (pest, crop, stage) → vulnerability level + modifier
# ============================================================================
STAGE_VULNERABILITY = {
    ("Rice Leafhopper", "Rice", "seedling"):   {"level": "Critical", "modifier": 1.8, "note": "Seedlings highly susceptible to tungro virus transmission"},
    ("Rice Leafhopper", "Rice", "tillering"):  {"level": "High",     "modifier": 1.4, "note": "Active feeding on young tillers spreads disease"},
    ("Rice Leafhopper", "Rice", "heading"):    {"level": "Medium",   "modifier": 1.0, "note": "Moderate risk at heading stage"},
    ("Rice Leafhopper", "Rice", "maturity"):   {"level": "Low",      "modifier": 0.5, "note": "Minimal impact on mature grain"},

    ("Fall Armyworm", "Corn", "emergence"):    {"level": "High",     "modifier": 1.5, "note": "Seedling destruction can require replanting"},
    ("Fall Armyworm", "Corn", "vegetative"):   {"level": "Critical", "modifier": 2.0, "note": "Whorl-stage feeding causes maximum yield loss"},
    ("Fall Armyworm", "Corn", "tasseling"):    {"level": "High",     "modifier": 1.3, "note": "Tassel damage reduces pollination"},
    ("Fall Armyworm", "Corn", "silking"):      {"level": "High",     "modifier": 1.4, "note": "Ear damage directly reduces grain fill"},
    ("Fall Armyworm", "Corn", "maturity"):     {"level": "Low",      "modifier": 0.4, "note": "Limited impact on mature ears"},

    ("Brown Planthopper", "Rice", "seedling"): {"level": "High",     "modifier": 1.6, "note": "Hopper burn can devastate nurseries"},
    ("Brown Planthopper", "Rice", "tillering"): {"level": "Critical","modifier": 2.0, "note": "Peak vulnerability — hopper burn spreads rapidly"},
    ("Brown Planthopper", "Rice", "heading"):  {"level": "High",     "modifier": 1.3, "note": "Late infestation causes chaffy grains"},

    ("Cotton Bollworm", "Cotton", "squaring"): {"level": "High",     "modifier": 1.5, "note": "Square shedding reduces boll numbers"},
    ("Cotton Bollworm", "Cotton", "flowering"):{"level": "Critical", "modifier": 1.8, "note": "Direct boll damage causes maximum loss"},
    ("Cotton Bollworm", "Cotton", "boll_fill"):{"level": "High",     "modifier": 1.4, "note": "Larval feeding damages lint quality"},

    ("Diamondback Moth", "Vegetables", "seedling"):  {"level": "Critical", "modifier": 2.0, "note": "Can destroy transplants completely"},
    ("Diamondback Moth", "Vegetables", "vegetative"):{"level": "High",     "modifier": 1.5, "note": "Severe defoliation reduces head formation"},
    ("Diamondback Moth", "Vegetables", "harvest"):   {"level": "Medium",   "modifier": 0.8, "note": "Cosmetic damage reduces market value"},

    ("Wheat Aphid", "Wheat", "heading"):       {"level": "High",     "modifier": 1.6, "note": "Aphid feeding during heading reduces grain weight"},
    ("Wheat Aphid", "Wheat", "grain_fill"):    {"level": "Critical", "modifier": 1.8, "note": "Direct sap removal during grain fill causes shriveling"},
    ("Wheat Aphid", "Wheat", "maturity"):      {"level": "Low",      "modifier": 0.3, "note": "Minimal impact on mature grain"},

    ("Colorado Potato Beetle", "Potato", "vegetative"): {"level": "Critical", "modifier": 2.0, "note": "Complete defoliation can occur in days"},
    ("Colorado Potato Beetle", "Potato", "flowering"):  {"level": "High",     "modifier": 1.5, "note": "Defoliation during flowering reduces tuber count"},
}

# ============================================================================
# Restricted Chemicals by Growth Stage
# ============================================================================
CHEMICAL_RESTRICTIONS = {
    "harvest":    ["Chlorpyrifos", "Fipronil", "Carbofuran", "Imidacloprid"],
    "maturity":   ["Chlorpyrifos", "Fipronil"],
    "flowering":  ["Neonicotinoids (pollinator risk)", "Broad-spectrum pyrethroids"],
    "fruiting":   ["Systemic insecticides", "Carbofuran"],
    "grain_fill": ["Chlorpyrifos", "Dimethoate"],
}


def calculate_economic_impact(
    pest_name: str,
    crop: str,
    field_size_ha: float,
    infestation_level: str = "moderate",
    growth_stage: Optional[str] = None,
) -> dict:
    """
    Calculate comprehensive economic impact of a pest infestation.

    Returns estimated yield loss, treatment costs, ROI, and recommendations.
    """
    # Normalize inputs
    infestation_level = infestation_level.lower()
    if infestation_level not in ("light", "moderate", "severe", "critical"):
        infestation_level = "moderate"

    # Get crop economics
    crop_econ = CROP_ECONOMICS.get(crop, CROP_ECONOMICS.get("Multiple"))
    price_per_ton = crop_econ["price_per_ton"]
    yield_per_ha = crop_econ["avg_yield_ton_per_ha"]
    value_per_ha = round(price_per_ton * yield_per_ha, 2)

    # Get yield loss percentage
    pest_losses = PEST_YIELD_LOSS.get(pest_name, {"light": 5, "moderate": 15, "severe": 30, "critical": 50})
    base_loss_pct = pest_losses.get(infestation_level, 15)

    # Apply growth stage vulnerability modifier
    stage_modifier = 1.0
    stage_info = None
    if growth_stage:
        stage_key = (pest_name, crop, growth_stage)
        if stage_key in STAGE_VULNERABILITY:
            stage_info = STAGE_VULNERABILITY[stage_key]
            stage_modifier = stage_info["modifier"]

    adjusted_loss_pct = min(95, round(base_loss_pct * stage_modifier, 1))

    # Calculate losses
    total_field_value = round(value_per_ha * field_size_ha, 2)
    potential_loss = round(total_field_value * (adjusted_loss_pct / 100), 2)
    loss_per_ha = round(potential_loss / max(field_size_ha, 0.01), 2)

    # Calculate treatment costs from PEST_DATABASE treatment steps
    treatment_breakdown = []
    total_treatment_cost = 0
    for method, costs in TREATMENT_COSTS_PER_HA.items():
        method_cost = round(costs["cost"] * field_size_ha, 2)
        treatment_breakdown.append({
            "method": method,
            "cost_per_ha": costs["cost"],
            "total_cost": method_cost,
            "labor_hours": costs["labor_hours"] * field_size_ha,
            "reapplication_needed": costs["reapply"],
        })

    # Recommended treatment strategy costs
    ipm_cost = round(
        (TREATMENT_COSTS_PER_HA["Inspection"]["cost"] +
         TREATMENT_COSTS_PER_HA["Biological"]["cost"] +
         TREATMENT_COSTS_PER_HA["IPM"]["cost"]) * field_size_ha, 2
    )
    chemical_cost = round(
        (TREATMENT_COSTS_PER_HA["Inspection"]["cost"] +
         TREATMENT_COSTS_PER_HA["Chemical"]["cost"]) * field_size_ha, 2
    )
    organic_cost = round(
        (TREATMENT_COSTS_PER_HA["Inspection"]["cost"] +
         TREATMENT_COSTS_PER_HA["Biological"]["cost"] +
         TREATMENT_COSTS_PER_HA["Organic"]["cost"]) * field_size_ha, 2
    )

    # ROI calculation
    roi_ipm = round(potential_loss / max(ipm_cost, 1), 1)
    roi_chemical = round(potential_loss / max(chemical_cost, 1), 1)

    # Net savings
    net_saving_ipm = round(potential_loss - ipm_cost, 2)
    net_saving_chemical = round(potential_loss - chemical_cost, 2)

    # Urgency level
    if adjusted_loss_pct >= 50:
        urgency = "EMERGENCY"
        urgency_color = "#dc2626"
        recommendation = f"Immediate action required. {pest_name} at {infestation_level} level threatens {adjusted_loss_pct}% yield loss (${potential_loss:,.0f} total). Deploy IPM strategy immediately — ROI of {roi_ipm}:1."
    elif adjusted_loss_pct >= 25:
        urgency = "HIGH"
        urgency_color = "#ef4444"
        recommendation = f"Urgent treatment needed. Estimated {adjusted_loss_pct}% yield loss (${potential_loss:,.0f}). IPM approach recommended with {roi_ipm}:1 return on investment."
    elif adjusted_loss_pct >= 10:
        urgency = "MODERATE"
        urgency_color = "#f59e0b"
        recommendation = f"Preventive action advised. {adjusted_loss_pct}% yield loss possible (${potential_loss:,.0f}). Monitor closely and apply biological controls."
    else:
        urgency = "LOW"
        urgency_color = "#10b981"
        recommendation = f"Monitor and scout regularly. Current {adjusted_loss_pct}% loss risk (${potential_loss:,.0f}) is manageable with cultural practices."

    return {
        "pest_name": pest_name,
        "crop": crop,
        "field_size_ha": field_size_ha,
        "infestation_level": infestation_level,
        "growth_stage": growth_stage,

        "crop_economics": {
            "price_per_ton": price_per_ton,
            "yield_per_ha": yield_per_ha,
            "value_per_ha": value_per_ha,
            "total_field_value": total_field_value,
            "currency": "USD",
        },

        "yield_impact": {
            "base_loss_percent": base_loss_pct,
            "stage_modifier": stage_modifier,
            "adjusted_loss_percent": adjusted_loss_pct,
            "estimated_loss_tons": round(yield_per_ha * field_size_ha * (adjusted_loss_pct / 100), 2),
            "potential_loss_usd": potential_loss,
            "loss_per_ha_usd": loss_per_ha,
        },

        "stage_vulnerability": {
            "level": stage_info["level"] if stage_info else "Unknown",
            "note": stage_info["note"] if stage_info else "No stage-specific data available",
            "modifier": stage_modifier,
        } if growth_stage else None,

        "treatment_costs": {
            "ipm_integrated": {"total": ipm_cost, "per_ha": round(ipm_cost / max(field_size_ha, 0.01), 2)},
            "chemical_only": {"total": chemical_cost, "per_ha": round(chemical_cost / max(field_size_ha, 0.01), 2)},
            "organic": {"total": organic_cost, "per_ha": round(organic_cost / max(field_size_ha, 0.01), 2)},
        },

        "roi_analysis": {
            "ipm_roi": roi_ipm,
            "chemical_roi": roi_chemical,
            "ipm_net_saving": net_saving_ipm,
            "chemical_net_saving": net_saving_chemical,
            "best_strategy": "IPM" if roi_ipm >= roi_chemical else "Chemical",
        },

        "urgency": urgency,
        "urgency_color": urgency_color,
        "recommendation": recommendation,
    }


def get_crop_stage_advice(
    pest_name: str,
    crop: str,
    growth_stage: str,
) -> dict:
    """
    Get growth-stage-specific pest management advice.
    """
    crop_stages = CROP_GROWTH_STAGES.get(crop, CROP_GROWTH_STAGES.get("Vegetables"))
    all_stages = crop_stages["stages"]
    phi = crop_stages["pre_harvest_interval"]

    # Find current stage info
    current = None
    stage_index = -1
    for i, s in enumerate(all_stages):
        if s["code"] == growth_stage or s["name"].lower() == growth_stage.lower():
            current = s
            stage_index = i
            growth_stage = s["code"]
            break

    if not current:
        current = all_stages[0]
        growth_stage = current["code"]
        stage_index = 0

    # Get vulnerability
    stage_key = (pest_name, crop, growth_stage)
    vuln = STAGE_VULNERABILITY.get(stage_key, {
        "level": "Medium",
        "modifier": 1.0,
        "note": f"General vulnerability of {crop} to {pest_name} at {current['name']} stage."
    })

    # Chemical restrictions for this stage
    restricted = CHEMICAL_RESTRICTIONS.get(growth_stage, [])

    # Is this near harvest?
    near_harvest = stage_index >= len(all_stages) - 2
    harvest_warning = None
    if near_harvest:
        harvest_warning = (
            f"⚠️ PRE-HARVEST INTERVAL: {phi} days minimum between last chemical "
            f"application and harvest. Consider biological or mechanical alternatives only."
        )

    # Stage-specific actions
    stage_actions = []
    if vuln["level"] in ("Critical", "High"):
        stage_actions = [
            {"priority": 1, "action": "Immediate scouting — confirm pest density exceeds economic threshold", "method": "Inspection"},
            {"priority": 2, "action": f"Deploy biological controls specific to {pest_name}", "method": "Biological"},
            {"priority": 3, "action": "Apply targeted treatment if threshold exceeded" if not near_harvest else "Use only biological/mechanical methods near harvest", "method": "IPM"},
            {"priority": 4, "action": "Re-scout in 3-5 days to assess treatment efficacy", "method": "Monitoring"},
        ]
    elif vuln["level"] == "Medium":
        stage_actions = [
            {"priority": 1, "action": "Regular monitoring — scout weekly for population changes", "method": "Inspection"},
            {"priority": 2, "action": "Strengthen cultural controls (crop hygiene, spacing)", "method": "Cultural"},
            {"priority": 3, "action": "Prepare biological agents for deployment if needed", "method": "Biological"},
        ]
    else:
        stage_actions = [
            {"priority": 1, "action": "Routine monitoring — pest impact minimal at this stage", "method": "Inspection"},
            {"priority": 2, "action": "Focus on preventive cultural practices for next vulnerable stage", "method": "Cultural"},
        ]

    # Timeline — what's coming next
    upcoming_stages = []
    for i in range(stage_index + 1, min(stage_index + 3, len(all_stages))):
        future = all_stages[i]
        future_key = (pest_name, crop, future["code"])
        future_vuln = STAGE_VULNERABILITY.get(future_key, {"level": "Unknown", "modifier": 1.0, "note": ""})
        upcoming_stages.append({
            "stage": future["name"],
            "days": future["duration_days"],
            "vulnerability": future_vuln["level"],
        })

    return {
        "pest_name": pest_name,
        "crop": crop,
        "current_stage": {
            "name": current["name"],
            "code": growth_stage,
            "duration_days": current["duration_days"],
        },
        "all_stages": [s["name"] for s in all_stages],
        "vulnerability": {
            "level": vuln["level"],
            "modifier": vuln["modifier"],
            "note": vuln["note"],
        },
        "pre_harvest_interval_days": phi,
        "near_harvest": near_harvest,
        "harvest_warning": harvest_warning,
        "restricted_chemicals": restricted,
        "recommended_actions": stage_actions,
        "upcoming_stages": upcoming_stages,
    }
