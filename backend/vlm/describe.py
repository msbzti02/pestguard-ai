"""
Vision-Language Model — Pest Image Description (describe.py)
=============================================================
Generates text descriptions of uploaded pest images using VLM.

Supports multiple backends with automatic failover:
    1. Google Gemini Vision (gemini-2.0-flash) — primary
    2. Groq Vision (llama-3.2-90b-vision) — fallback
    3. Mock description — last resort

Why VLM matters:
    The pest classifier (D3) only outputs a label like "Aphid".
    The VLM looks at the ACTUAL image and describes what it sees:
    "A cluster of small green insects on the underside of a rice leaf,
     with visible honeydew residue and leaf curling damage."

    This description is fed into the LLM prompt, giving it visual context
    that makes recommendations much more accurate and specific.

Usage:
    from vlm.describe import PestImageDescriber

    describer = PestImageDescriber()
    result = describer.describe("uploads/pest_photo.jpg")
    print(result["description"])
"""

import os
import sys
import base64
import random
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
from core.logger import get_logger

load_dotenv(Path(__file__).parent.parent / ".env")

log = get_logger("pestguard.vlm")


# ============================================================================
# Pest-specific prompt for VLM — guides the model to focus on agriculture
# ============================================================================
VLM_PROMPT = """Analyze this image of an insect or pest in an agricultural setting.
Provide a detailed description covering:

1. **Insect appearance**: Size estimate, color, body shape, wings, legs, antennae
2. **Behavior/position**: What is the insect doing? Where is it on the plant?
3. **Plant/crop condition**: What does the surrounding plant look like? Any visible damage?
4. **Damage indicators**: Leaf holes, discoloration, wilting, honeydew, frass, or other signs
5. **Environmental clues**: Lighting, moisture, season indicators if visible

Keep the description factual and concise (3-5 sentences).
If the image does NOT contain an insect or agricultural content, state that clearly.
Do NOT attempt to identify the species — just describe what you observe."""


class PestImageDescriber:
    """
    Multi-provider VLM for generating text descriptions of pest images.

    Tries providers in order:
        1. Google Gemini Vision (fast, accurate, free tier)
        2. Groq Vision (Llama 3.2 90B Vision)
        3. Mock fallback (hardcoded descriptions)
    """

    def __init__(self):
        self.providers = {}
        self._init_providers()

    def _init_providers(self):
        """Initialize all available VLM providers."""

        # Provider 1: Google Gemini Vision
        google_key = os.getenv("GOOGLE_API_KEY")
        if google_key:
            try:
                from google import genai
                client = genai.Client(api_key=google_key)
                self.providers["gemini"] = client
                log.info("Gemini Vision ready ✅")
            except Exception as exc:
                log.warning(f"Gemini Vision init failed: {exc}")

        # Provider 2: Groq Vision
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=groq_key)
                self.providers["groq"] = client
                log.info("Groq Vision ready ✅")
            except Exception as exc:
                log.warning(f"Groq Vision init failed: {exc}")

        provider_names = list(self.providers.keys()) or ["mock"]
        log.info(f"Active VLM providers: {', '.join(provider_names)}")

    def _load_image_bytes(self, image_path: str) -> bytes:
        """Load image file as bytes."""
        with open(image_path, "rb") as f:
            return f.read()

    def _load_image_base64(self, image_path: str) -> str:
        """Load image file as base64 string."""
        image_bytes = self._load_image_bytes(image_path)
        return base64.b64encode(image_bytes).decode("utf-8")

    def _get_mime_type(self, image_path: str) -> str:
        """Determine MIME type from file extension."""
        ext = Path(image_path).suffix.lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
        }
        return mime_map.get(ext, "image/jpeg")

    def describe(self, image_path: str) -> dict:
        """
        Generate a text description of a pest image.

        Tries VLM providers in failover order.

        Args:
            image_path: Path to the uploaded pest image

        Returns:
            dict with keys:
                - description: Text description of the image
                - provider: Which VLM provider was used
                - is_mock: Whether the description is a mock fallback
        """
        if not os.path.exists(image_path):
            return {
                "description": "Image file not found. Unable to generate visual description.",
                "provider": "error",
                "is_mock": True,
            }

        # Try each provider in order
        for provider_name in ["gemini", "groq"]:
            if provider_name not in self.providers:
                continue
            try:
                if provider_name == "gemini":
                    desc = self._describe_gemini(image_path)
                elif provider_name == "groq":
                    desc = self._describe_groq(image_path)
                else:
                    continue

                return {
                    "description": desc,
                    "provider": provider_name,
                    "is_mock": False,
                }

            except Exception as exc:
                log.warning(f"VLM provider {provider_name} failed: {exc}, trying next...")
                continue

        # All providers failed — return mock
        return self._mock_description()

    def _describe_gemini(self, image_path: str) -> str:
        """Generate description using Google Gemini Vision."""
        from google import genai
        from google.genai import types

        client = self.providers["gemini"]
        image_bytes = self._load_image_bytes(image_path)
        mime_type = self._get_mime_type(image_path)

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Content(
                    parts=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        types.Part.from_text(text=VLM_PROMPT),
                    ]
                )
            ],
        )
        return response.text.strip()

    def _describe_groq(self, image_path: str) -> str:
        """Generate description using Groq Vision (Llama 3.2 Vision)."""
        client = self.providers["groq"]
        image_b64 = self._load_image_base64(image_path)
        mime_type = self._get_mime_type(image_path)

        response = client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_b64}",
                            },
                        },
                        {
                            "type": "text",
                            "text": VLM_PROMPT,
                        },
                    ],
                }
            ],
            max_tokens=500,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()

    def _mock_description(self) -> dict:
        """Fallback mock descriptions when no VLM is available."""
        descriptions = [
            "A small green insect with translucent wings resting on a rice leaf. "
            "The leaf shows minor yellowing damage around the insect's position. "
            "Some honeydew residue is visible on the leaf surface.",

            "A brown caterpillar-like larva on the stem of a cereal plant. "
            "Visible feeding damage on the stem surface with small bore holes. "
            "The surrounding leaves show signs of wilting.",

            "A cluster of tiny aphids on the underside of a broad green leaf. "
            "Honeydew residue and early sooty mold are visible. "
            "The leaf edges are beginning to curl inward.",

            "A winged beetle with dark brown coloring sitting on a corn stalk. "
            "Small bore holes are visible on surrounding leaves. "
            "The plant appears to be at the vegetative growth stage.",
        ]
        return {
            "description": random.choice(descriptions),
            "provider": "mock",
            "is_mock": True,
        }

    def is_agricultural_image(self, image_path: str) -> dict:
        """
        PRE-FILTER: Check if an image contains agricultural/insect content.

        Uses VLM to analyze the image and determine if it's relevant.
        Rejects non-agricultural images (cars, selfies, random objects).

        Returns:
            dict with keys:
                - is_valid: True if image appears to contain insect/agricultural content
                - reason: Explanation of the decision
                - provider: Which VLM was used for the check
        """
        FILTER_PROMPT = (
            "Look at this image carefully. Does it contain ANY of the following?\n"
            "1. An insect, bug, or pest\n"
            "2. A plant, crop, leaf, or agricultural field\n"
            "3. Pest damage on vegetation\n\n"
            "Respond with EXACTLY one line:\n"
            "VALID: [brief reason] — if the image contains insects or agricultural content\n"
            "INVALID: [brief reason] — if the image does NOT contain insects or agricultural content"
        )

        for provider_name in ["gemini", "groq"]:
            if provider_name not in self.providers:
                continue
            try:
                if provider_name == "gemini":
                    from google.genai import types
                    client = self.providers["gemini"]
                    image_bytes = self._load_image_bytes(image_path)
                    mime_type = self._get_mime_type(image_path)

                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=[
                            types.Content(
                                parts=[
                                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                                    types.Part.from_text(text=FILTER_PROMPT),
                                ]
                            )
                        ],
                    )
                    result_text = response.text.strip()

                elif provider_name == "groq":
                    client = self.providers["groq"]
                    image_b64 = self._load_image_base64(image_path)
                    mime_type = self._get_mime_type(image_path)

                    response = client.chat.completions.create(
                        model="llama-3.2-90b-vision-preview",
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}},
                                {"type": "text", "text": FILTER_PROMPT},
                            ],
                        }],
                        max_tokens=100,
                        temperature=0.1,
                    )
                    result_text = response.choices[0].message.content.strip()

                # Parse response
                is_valid = result_text.upper().startswith("VALID")
                return {
                    "is_valid": is_valid,
                    "reason": result_text,
                    "provider": provider_name,
                }

            except Exception as exc:
                log.warning(f"VLM pre-filter {provider_name} failed: {exc}")
                continue

        # If all VLM providers fail, allow the image through (don't block users)
        return {
            "is_valid": True,
            "reason": "VLM pre-filter unavailable — image allowed by default.",
            "provider": "fallback",
        }


# ============================================================================
# Quick test
# ============================================================================
if __name__ == "__main__":
    print("Testing PestImageDescriber...\n")

    describer = PestImageDescriber()

    # Test with a sample image (if exists)
    test_images = list(Path("uploads").glob("*")) if Path("uploads").exists() else []

    if test_images:
        img = str(test_images[0])
        print(f"Describing: {img}")
        result = describer.describe(img)
        print(f"Provider: {result['provider']}")
        print(f"Description: {result['description'][:300]}")

        print(f"\nPre-filter check:")
        check = describer.is_agricultural_image(img)
        print(f"Valid: {check['is_valid']}")
        print(f"Reason: {check['reason']}")
    else:
        print("No test images found. Upload an image first.")
        result = describer._mock_description()
        print(f"Mock description: {result['description']}")
