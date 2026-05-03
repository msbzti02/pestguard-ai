"""
LLM Agent — Prompt Templates (prompts.py)
==========================================
Three carefully engineered prompts for the pest management chatbot:

1. HIGH_CONFIDENCE_PROMPT  — Confidence >= 0.70: Full recommendation
2. LOW_CONFIDENCE_PROMPT   — Confidence < 0.70: Warning + re-upload
3. FOLLOW_UP_PROMPT        — User uploads a second image: Compare with previous

Every prompt:
    - Uses RAG context (retrieved agricultural documents)
    - Includes pest prediction data
    - Includes weather context (if available)
    - ALWAYS ends with the legal disclaimer
    - Is grounded in verified FAO/CABI/PlantVillage knowledge
"""


# ============================================================================
# Legal Disclaimer — appears on EVERY response, non-negotiable
# ============================================================================
LEGAL_DISCLAIMER = (
    "\n\n---\n"
    "⚖️ **LEGAL DISCLAIMER:** This information is provided for educational "
    "and informational purposes ONLY. It does NOT constitute professional "
    "agricultural advice or a legal recommendation. Always consult a "
    "certified agricultural expert or local extension officer before "
    "applying any pesticide or treatment. Follow all product label "
    "instructions and local regulations. The system developers accept "
    "no liability for decisions made based on this output."
)


# ============================================================================
# System prompt — defines the agent's persona and behavior rules
# ============================================================================
SYSTEM_PROMPT = """You are an expert agricultural pest management assistant developed 
for the Deep Learning-Based Insect Pest Recognition System. Your role is to help 
farmers identify and manage insect pests safely and effectively.

STRICT RULES YOU MUST FOLLOW:
1. ONLY recommend pesticides and methods found in the provided agricultural knowledge base.
2. NEVER invent pesticide names, dosages, or application methods.
3. If the knowledge base doesn't have information about a specific pest, say so honestly.
4. ALWAYS mention both chemical AND biological/cultural control alternatives.
5. ALWAYS consider weather conditions when recommending spray timing.
6. ALWAYS include treatment timing advice.
7. NEVER provide advice without the legal disclaimer.
8. If confidence is below 70%, do NOT provide specific pest management advice.
9. Respond in a clear, structured format that a farmer can follow.
10. Use plain language — avoid overly technical jargon.

You have access to verified agricultural knowledge from FAO, CABI, PlantVillage, 
and other internationally recognized sources via the RAG system."""


# ============================================================================
# PROMPT 1: High Confidence (>= 0.70)
# Full pest management recommendation
# ============================================================================
HIGH_CONFIDENCE_PROMPT = """Based on the image analysis, the system has identified the pest with sufficient confidence to provide management recommendations.

**PEST DETECTION RESULTS:**
- Pest identified: {pest_name}
- Confidence level: {confidence:.0%}
- Affected crop: {crop}
- Category ID: {category_id}

{vlm_section}

**CURRENT WEATHER CONDITIONS:**
{weather_section}

**RETRIEVED AGRICULTURAL KNOWLEDGE:**
The following verified information was retrieved from our knowledge base:
{rag_context}

**FARMER'S QUESTION:**
{user_message}

---

Please provide a comprehensive, structured response following this EXACT format:

## 🔍 Pest Identification
Briefly describe the identified pest, its characteristics, and typical damage patterns.

## 🧪 Recommended Chemical Control
List 2-3 specific pesticides with:
- Active ingredient name
- Application method (foliar spray, granule, soil drench)
- Important application notes
ONLY recommend pesticides mentioned in the retrieved knowledge above.

## 🌿 Biological & Cultural Alternatives
List 2-3 non-chemical control methods:
- Natural predators or parasitoids
- Cultural practices (crop rotation, sanitation, etc.)
- Preventive measures

## ⏰ Treatment Timing
- Best time of day to apply
- Growth stage considerations
- Weather requirements for safe application
- Pre-harvest interval reminders

## ⚠️ Weather Advisory
Based on current conditions, advise whether spraying is safe right now.

## 💡 Additional Tips
Any relevant IPM (Integrated Pest Management) advice specific to this pest-crop combination."""


# ============================================================================
# PROMPT 2: Low Confidence (< 0.70)
# Warning only — no specific pest management advice
# ============================================================================
LOW_CONFIDENCE_PROMPT = """The pest detection system has returned a prediction with LOW CONFIDENCE. This means the system is NOT sufficiently certain about the pest identification.

**DETECTION RESULTS (UNRELIABLE):**
- Tentative pest: {pest_name}
- Confidence level: {confidence:.0%} ⚠️ (BELOW 70% THRESHOLD)
- This prediction may be INCORRECT.

{vlm_section}

**FARMER'S QUESTION:**
{user_message}

---

IMPORTANT: Because the confidence is below 70%, you MUST NOT provide specific pest management advice. Instead, respond following this EXACT format:

## ⚠️ Low Confidence Warning
Explain clearly that the system's prediction confidence of {confidence:.0%} is below the required 70% reliability threshold, and that providing pest management advice at this confidence level could lead to incorrect treatment and potential crop damage.

## 📸 How to Get Better Results
Provide specific, practical tips for taking a better photo:
1. Move closer to the insect (fill at least 50% of the frame)
2. Use good lighting — natural daylight is best, avoid shadows
3. Hold the camera steady — avoid blurry images
4. Photograph the insect from above AND from the side if possible
5. Include some of the affected plant/leaf in the photo for context
6. If the insect is very small, try using your phone's macro/zoom mode

## 🔍 General Identification Help
WITHOUT making a definitive identification, describe what general type of insect the image MIGHT show (based on the tentative prediction), and suggest the farmer compare their observation with common pests in their region.

## 👨‍🌾 What To Do Next
1. Upload a clearer, better-lit photo for re-analysis
2. If the pest is causing immediate damage, contact your local agricultural extension officer
3. Do NOT apply pesticides based on an uncertain identification"""


# ============================================================================
# PROMPT 3: Follow-up (second image from same session)
# Personalized comparison with previous result
# ============================================================================
FOLLOW_UP_PROMPT = """The farmer has uploaded a NEW image in the same session. This is a follow-up to a previous pest analysis.

**PREVIOUS ANALYSIS:**
- Previous pest identified: {previous_pest_name}
- Previous confidence: {previous_confidence:.0%}

**NEW ANALYSIS:**
- Current pest identified: {pest_name}
- Current confidence: {confidence:.0%}
- Affected crop: {crop}

{vlm_section}

**CURRENT WEATHER CONDITIONS:**
{weather_section}

**RETRIEVED AGRICULTURAL KNOWLEDGE:**
{rag_context}

**FARMER'S QUESTION:**
{user_message}

---

Please provide a PERSONALIZED response that:

## 📋 Comparison with Previous Upload
Compare the new result with the previous one:
- Are they the same pest or different?
- Has the confidence improved?
- What might explain any differences?

## 🔍 Current Pest Assessment
Based on the NEW prediction (if confidence >= 70%), provide the full management recommendation following the same structure as a standard recommendation: identification, chemical control, biological alternatives, timing, and weather advisory.

If the new confidence is STILL below 70%, explain this and encourage another attempt with better photo quality.

## 💡 Session Summary
Summarize what we know from both uploads and provide the most helpful overall advice."""


# ============================================================================
# Helper functions to build prompt sections
# ============================================================================
def build_vlm_section(vlm_description: str = None) -> str:
    """Build the VLM visual description section for the prompt."""
    if vlm_description and vlm_description.strip():
        return (
            f"**VISUAL DESCRIPTION OF UPLOADED IMAGE:**\n"
            f"{vlm_description}\n"
            f"(Generated by Vision-Language Model analysis of the uploaded photo)"
        )
    return "**VISUAL DESCRIPTION:** Not available for this image."


def build_weather_section(weather_data: dict = None) -> str:
    """Build the weather context section for the prompt."""
    if not weather_data:
        return "Weather data not available. Provide general spraying safety guidelines."

    safe_status = "✅ SAFE to spray" if weather_data.get("safe_to_spray") else "❌ NOT SAFE to spray"

    alerts_text = ""
    if weather_data.get("alerts"):
        alerts_text = f"\n- Active alerts: {', '.join(weather_data['alerts'])}"

    return (
        f"- Temperature: {weather_data.get('temperature', 'N/A')}°C\n"
        f"- Humidity: {weather_data.get('humidity', 'N/A')}%\n"
        f"- Wind speed: {weather_data.get('wind_speed', 'N/A')} km/h\n"
        f"- Rain probability: {weather_data.get('rain_probability', 'N/A')}%\n"
        f"- Conditions: {weather_data.get('condition', 'N/A')}\n"
        f"- Spray safety: {safe_status}"
        f"{alerts_text}\n"
        f"- ⚠️ Note: Weather data reflects broad regional forecasts. "
        f"Actual field conditions may differ."
    )


def format_prompt(
    template: str,
    pest_name: str = "Unknown",
    confidence: float = 0.0,
    crop: str = "Unknown",
    category_id: int = -1,
    user_message: str = "",
    rag_context: str = "",
    vlm_description: str = None,
    weather_data: dict = None,
    previous_pest_name: str = None,
    previous_confidence: float = None,
) -> str:
    """
    Fill in a prompt template with all available data.

    This is the main function called by the chatbot to assemble the final prompt.
    """
    vlm_section = build_vlm_section(vlm_description)
    weather_section = build_weather_section(weather_data)

    # Build format kwargs
    kwargs = {
        "pest_name": pest_name,
        "confidence": confidence,
        "crop": crop,
        "category_id": category_id,
        "user_message": user_message,
        "rag_context": rag_context if rag_context else "No relevant knowledge retrieved.",
        "vlm_section": vlm_section,
        "weather_section": weather_section,
    }

    # Add follow-up fields if provided
    if previous_pest_name is not None:
        kwargs["previous_pest_name"] = previous_pest_name
        kwargs["previous_confidence"] = previous_confidence or 0.0

    return template.format(**kwargs)
