"""
LLM Agent — Chatbot Engine (chatbot.py)
========================================
The core decision support agent that combines:
    - RAG retrieval (agricultural knowledge)
    - LLM reasoning (Google Gemini or OpenAI)
    - Weather context
    - VLM descriptions
    - Session memory (personalized follow-ups)

This is the BRAIN of Department 2's system.

Usage:
    from agent.chatbot import PestManagementAgent

    agent = PestManagementAgent()
    response = agent.chat(
        message="How do I treat this?",
        pest_name="Aphid",
        confidence=0.91,
    )
    print(response["reply"])
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from rag.retriever import PestKnowledgeRetriever
from agent.prompts import (
    SYSTEM_PROMPT,
    HIGH_CONFIDENCE_PROMPT,
    LOW_CONFIDENCE_PROMPT,
    FOLLOW_UP_PROMPT,
    GENERAL_QUESTION_PROMPT,
    LEGAL_DISCLAIMER,
    format_prompt,
    build_weather_section,
)
from core.logger import get_logger
from core.retry import retry_with_backoff

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

log = get_logger("pestguard.agent")


# ============================================================================
# LLM Backend — supports Google Gemini, Groq (Llama), with auto-failover
# ============================================================================
class LLMBackend:
    """
    Multi-provider LLM backend with automatic failover.

    Initialization: loads ALL available providers at startup.
    Generation: tries providers in order (Gemini → Groq → Fallback).
    If one fails at runtime, automatically tries the next.
    """

    def __init__(self):
        self.providers = {}  # {name: model_object}
        self.primary = None  # Name of the primary provider
        self.provider = None  # Name of the provider that was actually used last
        self._init_all_providers()

    def _init_all_providers(self):
        """Initialize ALL available LLM providers."""

        # Provider 1: Google Gemini (via google-genai, the new SDK)
        google_key = os.getenv("GOOGLE_API_KEY")
        if google_key:
            try:
                from google import genai
                client = genai.Client(api_key=google_key)
                self.providers["gemini"] = client
                log.info("Gemini LLM ready (gemini-2.0-flash) ✅")
            except Exception as exc:
                log.warning(f"Gemini LLM init failed: {exc}")

        # Provider 2: Groq (fast Llama inference)
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=groq_key)
                self.providers["groq"] = client
                log.info("Groq LLM ready (llama-3.3-70b-versatile) ✅")
            except Exception as exc:
                log.warning(f"Groq LLM init failed: {exc}")

        # Set primary provider (first available)
        if "gemini" in self.providers:
            self.primary = "gemini"
        elif "groq" in self.providers:
            self.primary = "groq"
        else:
            self.primary = "fallback"

        provider_names = list(self.providers.keys()) or ["fallback"]
        log.info(f"Active LLM providers: {', '.join(provider_names)} | Primary: {self.primary}")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate a response, trying providers in failover order.
        Gemini → Groq → Fallback.
        """
        # Try each provider in order
        for provider_name in ["gemini", "groq"]:
            if provider_name not in self.providers:
                continue
            try:
                if provider_name == "gemini":
                    result = self._generate_gemini(system_prompt, user_prompt)
                elif provider_name == "groq":
                    result = self._generate_groq(system_prompt, user_prompt)
                else:
                    continue

                self.provider = provider_name
                return result

            except Exception as exc:
                log.warning(f"LLM {provider_name} failed: {exc}, trying next...")
                continue

        # All providers failed
        self.provider = "fallback"
        return self._generate_fallback(user_prompt)

    @retry_with_backoff(max_attempts=3, base_delay=1.0, label="Gemini")
    def _generate_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """Generate using Google Gemini API (new google-genai SDK) — retried up to 3×."""
        client = self.providers["gemini"]
        full_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt,
        )
        return response.text

    @retry_with_backoff(max_attempts=3, base_delay=1.0, label="Groq")
    def _generate_groq(self, system_prompt: str, user_prompt: str) -> str:
        """Generate using Groq API (fast Llama 3.3 70B inference) — retried up to 3×."""
        client = self.providers["groq"]
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=2000,
            temperature=0.3,
        )
        return response.choices[0].message.content

    def _generate_fallback(self, user_prompt: str) -> str:
        """Template-based fallback when no LLM API is available."""
        return (
            "## ⚠️ LLM Service Unavailable\n\n"
            "All LLM providers failed. Please check your API keys in `.env`:\n\n"
            "```\n"
            "GOOGLE_API_KEY=your-gemini-key\n"
            "GROQ_API_KEY=your-groq-key\n"
            "```\n\n"
            "The RAG system still retrieved relevant agricultural knowledge. "
            "Please fix the API keys to enable AI-powered recommendations."
        )


# ============================================================================
# Session Memory — tracks user interactions for personalized feedback
# ============================================================================
class SessionMemory:
    """
    Stores per-session interaction history for personalized follow-up responses.
    When a user uploads multiple images, the agent references previous results.
    """

    def __init__(self):
        self.sessions = {}  # {session_id: [list of interactions]}

    def get_session(self, session_id: str) -> list:
        """Get all interactions for a session."""
        return self.sessions.get(session_id, [])

    def get_last_interaction(self, session_id: str) -> Optional[dict]:
        """Get the most recent interaction for a session."""
        session = self.sessions.get(session_id, [])
        return session[-1] if session else None

    def add_interaction(self, session_id: str, interaction: dict):
        """Record a new interaction in the session."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append({
            **interaction,
            "timestamp": datetime.now().isoformat(),
        })

    def has_previous(self, session_id: str) -> bool:
        """Check if there are previous interactions in this session."""
        return len(self.sessions.get(session_id, [])) > 0


# ============================================================================
# Main Agent — PestManagementAgent
# ============================================================================
class PestManagementAgent:
    """
    The complete pest management decision support agent.

    Combines RAG retrieval, LLM reasoning, weather awareness,
    and session memory into a single chat interface.

    Usage:
        agent = PestManagementAgent()

        # High-confidence pest query
        result = agent.chat(
            message="How do I treat this pest?",
            pest_name="Aphid",
            confidence=0.91,
            crop="Rice",
        )

        # Low-confidence query
        result = agent.chat(
            message="What is this bug?",
            confidence=0.45,
        )
    """

    def __init__(self):
        """Initialize all components of the agent."""
        print("\n[Agent] Initializing Pest Management Agent...")

        # RAG Retriever
        self.retriever = PestKnowledgeRetriever()
        if self.retriever.is_ready():
            stats = self.retriever.get_stats()
            log.info(f"RAG ready: {stats['total_chunks']} knowledge chunks")
        else:
            log.warning("RAG index not built. Run 'python rag/build_index.py'")

        # LLM Backend
        self.llm = LLMBackend()

        # Session Memory
        self.memory = SessionMemory()

        print("[Agent] Initialization complete.\n")

    def chat(
        self,
        message: str,
        session_id: str = "default",
        pest_name: str = None,
        confidence: float = None,
        crop: str = None,
        category_id: int = None,
        vlm_description: str = None,
        weather_data: dict = None,
    ) -> dict:
        """
        Process a user message and generate an agricultural recommendation.

        This is the main entry point for the chatbot. It:
        1. Determines which prompt template to use (high/low/follow-up)
        2. Retrieves relevant knowledge from RAG
        3. Builds the full prompt with all context
        4. Sends to the LLM for response generation
        5. Appends the legal disclaimer
        6. Records the interaction in session memory

        Args:
            message: The farmer's question
            session_id: Unique session identifier for personalized follow-ups
            pest_name: Name of the predicted pest (from D3 model)
            confidence: Prediction confidence (0.0 to 1.0)
            crop: Affected crop type
            category_id: IP102 category ID
            vlm_description: Visual description from VLM (BLIP-2/LLaVA)
            weather_data: Weather dict with temperature, wind, rain, etc.

        Returns:
            dict with keys:
                - reply: The full LLM response with disclaimer
                - disclaimer: The legal disclaimer text
                - is_low_confidence: Whether confidence was < 0.70
                - rag_sources: List of source documents used
                - weather_warning: Weather safety warning (if applicable)
                - session_id: The session ID used
                - prompt_type: Which template was used
                - llm_provider: Which LLM backend was used
        """

        # Determine if this is a general question (no image context)
        is_general_question = (
            (pest_name is None or pest_name == "Unknown") and
            (confidence is None or confidence == 0.0)
        )

        # Determine confidence status (only when pest context exists)
        is_low_confidence = (
            not is_general_question and
            confidence is not None and confidence < 0.70
        )

        # ── Step 1: Retrieve relevant knowledge from RAG ──
        rag_context = ""
        rag_sources = []
        if self.retriever.is_ready():
            # Build a rich query combining pest name, crop, and user question
            query_parts = []
            if pest_name and pest_name != "Unknown" and pest_name != "Uncertain":
                query_parts.append(pest_name)
            if crop and crop != "Unknown":
                query_parts.append(crop)
            query_parts.append(message)
            search_query = " ".join(query_parts)

            # Retrieve with sources for metadata
            retrieval = self.retriever.retrieve_with_sources(search_query, top_k=5)
            rag_context = self.retriever.retrieve(search_query, top_k=5)
            rag_sources = [
                {"source": c["source_file"], "page": c["page"]}
                for c in retrieval["chunks"]
            ]

        # ── Step 2: Select the appropriate prompt template ──
        previous = self.memory.get_last_interaction(session_id)

        if is_general_question:
            # No image uploaded — answer as a general agricultural Q&A
            weather_block = ""
            if weather_data:
                weather_block = (
                    "**CURRENT WEATHER CONDITIONS:**\n"
                    + build_weather_section(weather_data)
                )
            user_prompt = GENERAL_QUESTION_PROMPT.format(
                rag_context=rag_context if rag_context else "No relevant knowledge retrieved.",
                weather_section_block=weather_block,
                user_message=message,
            )
            prompt_type = "general_question"
        elif is_low_confidence:
            template = LOW_CONFIDENCE_PROMPT
            prompt_type = "low_confidence"
            user_prompt = format_prompt(
                template=template,
                pest_name=pest_name or "Unknown",
                confidence=confidence or 0.0,
                crop=crop or "Unknown",
                category_id=category_id or -1,
                user_message=message,
                rag_context=rag_context,
                vlm_description=vlm_description,
                weather_data=weather_data,
                previous_pest_name=previous.get("pest_name") if previous else None,
                previous_confidence=previous.get("confidence") if previous else None,
            )
        elif previous and previous.get("pest_name"):
            template = FOLLOW_UP_PROMPT
            prompt_type = "follow_up"
            user_prompt = format_prompt(
                template=template,
                pest_name=pest_name or "Unknown",
                confidence=confidence or 0.0,
                crop=crop or "Unknown",
                category_id=category_id or -1,
                user_message=message,
                rag_context=rag_context,
                vlm_description=vlm_description,
                weather_data=weather_data,
                previous_pest_name=previous.get("pest_name") if previous else None,
                previous_confidence=previous.get("confidence") if previous else None,
            )
        else:
            template = HIGH_CONFIDENCE_PROMPT
            prompt_type = "high_confidence"
            user_prompt = format_prompt(
                template=template,
                pest_name=pest_name or "Unknown",
                confidence=confidence or 0.0,
                crop=crop or "Unknown",
                category_id=category_id or -1,
                user_message=message,
                rag_context=rag_context,
                vlm_description=vlm_description,
                weather_data=weather_data,
                previous_pest_name=previous.get("pest_name") if previous else None,
                previous_confidence=previous.get("confidence") if previous else None,
            )

        # ── Step 4: Generate LLM response ──
        llm_response = self.llm.generate(SYSTEM_PROMPT, user_prompt)

        # ── Step 5: Append legal disclaimer ──
        full_reply = llm_response + LEGAL_DISCLAIMER

        # ── Step 6: Check for weather warnings ──
        weather_warning = None
        if weather_data and not weather_data.get("safe_to_spray", True):
            alerts = weather_data.get("alerts", [])
            condition = weather_data.get("condition", "Unknown")
            weather_warning = (
                f"🌧️ WEATHER ALERT: {', '.join(alerts) if alerts else condition}. "
                f"Current conditions are NOT safe for pesticide application. "
                f"Do NOT spray until conditions improve."
            )

        # ── Step 7: Record interaction in session memory ──
        self.memory.add_interaction(session_id, {
            "message": message,
            "pest_name": pest_name,
            "confidence": confidence,
            "crop": crop,
            "prompt_type": prompt_type,
        })

        return {
            "reply": full_reply,
            "disclaimer": LEGAL_DISCLAIMER,
            "is_low_confidence": is_low_confidence,
            "rag_sources": rag_sources,
            "weather_warning": weather_warning,
            "session_id": session_id,
            "prompt_type": prompt_type,
            "llm_provider": self.llm.provider,
        }


# ============================================================================
# Quick test
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  Testing PestManagementAgent")
    print("=" * 60)

    agent = PestManagementAgent()

    # Test 1: High confidence
    print("\n--- TEST 1: High Confidence ---")
    result = agent.chat(
        message="How do I treat aphids on my rice field?",
        pest_name="Aphid",
        confidence=0.91,
        crop="Rice",
        session_id="test-1",
    )
    print(f"Type: {result['prompt_type']}")
    print(f"LLM: {result['llm_provider']}")
    print(f"Sources: {[s['source'] for s in result['rag_sources']]}")
    print(f"Reply (first 300 chars): {result['reply'][:300]}...")

    # Test 2: Low confidence
    print("\n--- TEST 2: Low Confidence ---")
    result = agent.chat(
        message="What is this bug?",
        confidence=0.45,
        session_id="test-2",
    )
    print(f"Type: {result['prompt_type']}")
    print(f"Low confidence: {result['is_low_confidence']}")
    print(f"Reply (first 300 chars): {result['reply'][:300]}...")

    # Test 3: Follow-up (same session as test 1)
    print("\n--- TEST 3: Follow-up ---")
    result = agent.chat(
        message="I uploaded a better photo, what about this one?",
        pest_name="Rice Leaf Roller",
        confidence=0.85,
        crop="Rice",
        session_id="test-1",  # Same session!
    )
    print(f"Type: {result['prompt_type']}")
    print(f"Reply (first 300 chars): {result['reply'][:300]}...")

    print("\nAll tests completed!")
