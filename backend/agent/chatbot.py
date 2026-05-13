"""
LLM Agent — Chatbot Engine (chatbot.py)
========================================
The core decision support agent that combines:
    - RAG retrieval (agricultural knowledge)
    - LLM reasoning (6-provider failover chain)
    - Weather context
    - VLM descriptions
    - Multi-turn conversation memory
    - Response caching
    - Analytics tracking

This is the BRAIN of Department 2's system.

Providers (in failover order):
    1. Google Gemini 2.0 Flash
    2. Groq (Llama 3.3 70B)
    3. OpenRouter (free models)
    4. Together AI (Llama 3.1 8B)
    5. Cohere (Command R)
    6. Mistral AI (Mistral Small)
    → Mock fallback (extracts RAG text)
"""

import os
import sys
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

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

load_dotenv(Path(__file__).parent.parent / ".env")
log = get_logger("pestguard.agent")


# ============================================================================
# Analytics Tracker
# ============================================================================
class ChatAnalytics:
    """Tracks chat usage metrics for dashboard display."""

    def __init__(self):
        self.total_messages = 0
        self.total_responses = 0
        self.total_response_time = 0.0
        self.provider_usage = {}
        self.prompt_type_counts = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.errors = 0
        self.started_at = datetime.now().isoformat()

    def record(self, provider: str, prompt_type: str, response_time: float):
        self.total_messages += 1
        self.total_responses += 1
        self.total_response_time += response_time
        self.provider_usage[provider] = self.provider_usage.get(provider, 0) + 1
        self.prompt_type_counts[prompt_type] = self.prompt_type_counts.get(prompt_type, 0) + 1

    def to_dict(self) -> dict:
        avg_time = (self.total_response_time / self.total_responses) if self.total_responses > 0 else 0
        return {
            "total_messages": self.total_messages,
            "avg_response_time": round(avg_time, 2),
            "provider_usage": self.provider_usage,
            "prompt_type_counts": self.prompt_type_counts,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "errors": self.errors,
            "started_at": self.started_at,
        }


# ============================================================================
# Response Cache
# ============================================================================
class ResponseCache:
    """Simple in-memory LRU cache for LLM responses."""

    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size

    def _key(self, prompt: str) -> str:
        return hashlib.md5(prompt.encode()).hexdigest()

    def get(self, prompt: str) -> Optional[str]:
        k = self._key(prompt)
        if k in self.cache:
            self.cache[k]["hits"] += 1
            return self.cache[k]["response"]
        return None

    def put(self, prompt: str, response: str):
        if len(self.cache) >= self.max_size:
            oldest = min(self.cache, key=lambda k: self.cache[k]["time"])
            del self.cache[oldest]
        self.cache[self._key(prompt)] = {
            "response": response, "time": time.time(), "hits": 0
        }


# ============================================================================
# LLM Backend — 6 providers with automatic failover
# ============================================================================
class LLMBackend:
    """
    Multi-provider LLM backend with automatic failover.
    Tries providers in order: Gemini → Groq → OpenRouter → Together → Cohere → Mistral → Fallback.
    """

    def __init__(self):
        self.providers = {}
        self.primary = None
        self.provider = None
        self._init_all_providers()

    def _init_all_providers(self):
        """Initialize ALL available LLM providers."""

        # Provider 1: Google Gemini
        google_key = os.getenv("GOOGLE_API_KEY")
        if google_key:
            try:
                from google import genai
                client = genai.Client(api_key=google_key)
                self.providers["gemini"] = client
                log.info("Gemini LLM ready (gemini-2.0-flash) ✅")
            except Exception as exc:
                log.warning(f"Gemini LLM init failed: {exc}")

        # Provider 2: Groq
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=groq_key)
                self.providers["groq"] = client
                log.info("Groq LLM ready (llama-3.3-70b-versatile) ✅")
            except Exception as exc:
                log.warning(f"Groq LLM init failed: {exc}")

        # Provider 3: OpenRouter (free models)
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            try:
                import httpx
                self.providers["openrouter"] = {"key": openrouter_key}
                log.info("OpenRouter LLM ready ✅")
            except Exception as exc:
                log.warning(f"OpenRouter init failed: {exc}")

        # Provider 4: Together AI
        together_key = os.getenv("TOGETHER_API_KEY")
        if together_key:
            try:
                import httpx
                self.providers["together"] = {"key": together_key}
                log.info("Together AI LLM ready ✅")
            except Exception as exc:
                log.warning(f"Together AI init failed: {exc}")

        # Provider 5: Cohere
        cohere_key = os.getenv("COHERE_API_KEY")
        if cohere_key:
            try:
                import httpx
                self.providers["cohere"] = {"key": cohere_key}
                log.info("Cohere LLM ready ✅")
            except Exception as exc:
                log.warning(f"Cohere init failed: {exc}")

        # Provider 6: Mistral AI
        mistral_key = os.getenv("MISTRAL_API_KEY")
        if mistral_key:
            try:
                import httpx
                self.providers["mistral"] = {"key": mistral_key}
                log.info("Mistral AI LLM ready ✅")
            except Exception as exc:
                log.warning(f"Mistral init failed: {exc}")

        # Provider 7: Cerebras (fastest free LLM API)
        cerebras_key = os.getenv("CEREBRAS_API_KEY")
        if cerebras_key:
            try:
                import httpx
                self.providers["cerebras"] = {"key": cerebras_key}
                log.info("Cerebras LLM ready (llama-3.3-70b) ✅")
            except Exception as exc:
                log.warning(f"Cerebras init failed: {exc}")

        # Set primary provider
        provider_order = ["gemini", "groq", "openrouter", "together", "cohere", "mistral", "cerebras"]
        self.primary = next((p for p in provider_order if p in self.providers), "fallback")
        names = list(self.providers.keys()) or ["fallback"]
        log.info(f"Active LLM providers: {', '.join(names)} | Primary: {self.primary}")

    def get_provider_count(self) -> int:
        return len(self.providers)

    def generate(self, system_prompt: str, user_prompt: str, history: list = None) -> str:
        """Generate a response, trying providers in failover order."""
        provider_order = ["gemini", "groq", "openrouter", "together", "cohere", "mistral", "cerebras"]
        for name in provider_order:
            if name not in self.providers:
                continue
            try:
                if name == "gemini":
                    result = self._generate_gemini(system_prompt, user_prompt, history)
                elif name == "groq":
                    result = self._generate_groq(system_prompt, user_prompt, history)
                elif name == "openrouter":
                    result = self._generate_openrouter(system_prompt, user_prompt, history)
                elif name == "together":
                    result = self._generate_together(system_prompt, user_prompt, history)
                elif name == "cohere":
                    result = self._generate_cohere(system_prompt, user_prompt, history)
                elif name == "mistral":
                    result = self._generate_mistral(system_prompt, user_prompt, history)
                elif name == "cerebras":
                    result = self._generate_cerebras(system_prompt, user_prompt, history)
                else:
                    continue
                self.provider = name
                return result
            except Exception as exc:
                log.warning(f"LLM {name} failed ({type(exc).__name__}): {exc}")
                continue

        self.provider = "fallback"
        return self._generate_fallback(user_prompt)

    def _build_messages(self, system_prompt: str, user_prompt: str, history: list = None) -> list:
        """Build message list with optional conversation history."""
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for msg in history[-10:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_prompt})
        return messages

    @retry_with_backoff(max_attempts=2, base_delay=1.0, label="Gemini")
    def _generate_gemini(self, system_prompt: str, user_prompt: str, history: list = None) -> str:
        client = self.providers["gemini"]
        if history:
            hist_text = "\n".join([f"{'User' if m['role']=='user' else 'Assistant'}: {m['content']}" for m in history[-6:]])
            full = f"{system_prompt}\n\n--- CONVERSATION HISTORY ---\n{hist_text}\n\n--- CURRENT MESSAGE ---\n{user_prompt}"
        else:
            full = f"{system_prompt}\n\n---\n\n{user_prompt}"
        response = client.models.generate_content(model="gemini-2.0-flash", contents=full)
        return response.text

    @retry_with_backoff(max_attempts=2, base_delay=1.0, label="Groq")
    def _generate_groq(self, system_prompt: str, user_prompt: str, history: list = None) -> str:
        client = self.providers["groq"]
        msgs = self._build_messages(system_prompt, user_prompt, history)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", messages=msgs,
            max_tokens=2000, temperature=0.3,
        )
        return response.choices[0].message.content

    @retry_with_backoff(max_attempts=2, base_delay=1.0, label="OpenRouter")
    def _generate_openrouter(self, system_prompt: str, user_prompt: str, history: list = None) -> str:
        import httpx
        key = self.providers["openrouter"]["key"]
        msgs = self._build_messages(system_prompt, user_prompt, history)
        r = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "meta-llama/llama-3.1-8b-instruct:free", "messages": msgs, "max_tokens": 2000},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    @retry_with_backoff(max_attempts=2, base_delay=1.0, label="Together")
    def _generate_together(self, system_prompt: str, user_prompt: str, history: list = None) -> str:
        import httpx
        key = self.providers["together"]["key"]
        msgs = self._build_messages(system_prompt, user_prompt, history)
        r = httpx.post(
            "https://api.together.xyz/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo", "messages": msgs, "max_tokens": 2000},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    @retry_with_backoff(max_attempts=2, base_delay=1.0, label="Cohere")
    def _generate_cohere(self, system_prompt: str, user_prompt: str, history: list = None) -> str:
        import httpx
        key = self.providers["cohere"]["key"]
        msgs = self._build_messages(system_prompt, user_prompt, history)
        r = httpx.post(
            "https://api.cohere.com/v2/chat",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "command-a-03-2025", "messages": msgs, "max_tokens": 2000},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["message"]["content"][0]["text"]

    @retry_with_backoff(max_attempts=2, base_delay=1.0, label="Mistral")
    def _generate_mistral(self, system_prompt: str, user_prompt: str, history: list = None) -> str:
        import httpx
        key = self.providers["mistral"]["key"]
        msgs = self._build_messages(system_prompt, user_prompt, history)
        r = httpx.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "mistral-small-latest", "messages": msgs, "max_tokens": 2000},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    @retry_with_backoff(max_attempts=2, base_delay=1.0, label="Cerebras")
    def _generate_cerebras(self, system_prompt: str, user_prompt: str, history: list = None) -> str:
        import httpx
        key = self.providers["cerebras"]["key"]
        msgs = self._build_messages(system_prompt, user_prompt, history)
        r = httpx.post(
            "https://api.cerebras.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "llama3.1-8b", "messages": msgs, "max_tokens": 2000},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    def _generate_fallback(self, user_prompt: str) -> str:
        rag_start = user_prompt.find("AGRICULTURAL KNOWLEDGE")
        rag_end = user_prompt.find("---", rag_start + 1) if rag_start != -1 else -1
        if rag_start != -1 and rag_end != -1:
            rag_text = user_prompt[rag_start:rag_end].strip()
            lines = [l.strip() for l in rag_text.split("\n") if l.strip() and not l.startswith("AGRICULTURAL")]
            knowledge = "\n".join(lines[:15])
            return (
                "## 📚 Based on Our Knowledge Base\n\n"
                "Our AI advisor is temporarily busy. Here is relevant information "
                "from our agricultural knowledge database:\n\n"
                f"{knowledge}\n\n"
                "**💡 Tip:** Please try asking again in a moment for a more detailed, "
                "AI-generated response."
            )
        return (
            "## ⏳ AI Advisor Temporarily Busy\n\n"
            "Our AI models are currently experiencing high demand. "
            "Please try again in a few seconds.\n\n"
            "**In the meantime, you can:**\n"
            "- Check the **Weather & Spray Safety** page for current conditions\n"
            "- Upload a pest image for **instant identification**\n"
            "- View the **Outbreak Map** for regional reports"
        )


# ============================================================================
# Session Memory — multi-turn conversation tracking
# ============================================================================
class SessionMemory:
    """Stores per-session interaction history including full conversation for multi-turn."""

    def __init__(self):
        self.sessions = {}
        self.conversations = {}  # session_id → [{role, content}] for multi-turn

    def get_session(self, session_id: str) -> list:
        return self.sessions.get(session_id, [])

    def get_last_interaction(self, session_id: str) -> Optional[dict]:
        session = self.sessions.get(session_id, [])
        return session[-1] if session else None

    def add_interaction(self, session_id: str, interaction: dict):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append({
            **interaction, "timestamp": datetime.now().isoformat(),
        })

    def has_previous(self, session_id: str) -> bool:
        return len(self.sessions.get(session_id, [])) > 0

    def get_conversation(self, session_id: str) -> list:
        """Get multi-turn conversation history for LLM context."""
        return self.conversations.get(session_id, [])

    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to the multi-turn conversation history."""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        self.conversations[session_id].append({"role": role, "content": content})
        # Keep only last 10 messages to avoid token overflow
        if len(self.conversations[session_id]) > 10:
            self.conversations[session_id] = self.conversations[session_id][-10:]


# ============================================================================
# Main Agent — PestManagementAgent
# ============================================================================
class PestManagementAgent:
    """
    The complete pest management decision support agent.
    Combines RAG retrieval, multi-turn LLM reasoning, weather awareness,
    response caching, analytics tracking, and session memory.
    """

    def __init__(self):
        print("\n[Agent] Initializing Pest Management Agent...")
        self.retriever = PestKnowledgeRetriever()
        if self.retriever.is_ready():
            stats = self.retriever.get_stats()
            log.info(f"RAG ready: {stats['total_chunks']} knowledge chunks")
        else:
            log.warning("RAG index not built. Run 'python rag/build_index.py'")

        self.llm = LLMBackend()
        self.memory = SessionMemory()
        self.cache = ResponseCache(max_size=200)
        self.analytics = ChatAnalytics()
        self.language = "English"
        print("[Agent] Initialization complete.\n")

    def get_provider_count(self) -> int:
        return self.llm.get_provider_count()

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
        language: str = "English",
    ) -> dict:
        """
        Process a user message and generate an agricultural recommendation.
        Now with multi-turn memory, caching, analytics, quality scoring,
        and follow-up suggestion generation.
        """
        t_start = time.time()
        self.language = language

        # Add user message to multi-turn conversation
        self.memory.add_message(session_id, "user", message)

        is_general_question = (
            (pest_name is None or pest_name == "Unknown") and
            (confidence is None or confidence == 0.0)
        )
        is_low_confidence = (
            not is_general_question and
            confidence is not None and confidence < 0.70
        )

        # ── Step 1: RAG Retrieval ──
        rag_context = ""
        rag_sources = []
        rag_distances = []
        if self.retriever.is_ready():
            query_parts = []
            if pest_name and pest_name not in ("Unknown", "Uncertain"):
                query_parts.append(pest_name)
            if crop and crop != "Unknown":
                query_parts.append(crop)
            query_parts.append(message)
            search_query = " ".join(query_parts)
            
            search_query = self.retriever.expand_query(search_query, pest_name=pest_name)

            retrieval = self.retriever.retrieve_with_sources(search_query, top_k=5)
            rag_context = self.retriever.retrieve_with_rerank(search_query, top_k=5, candidate_k=15)
            rag_sources = [
                {"source": c["source_file"], "page": c["page"]}
                for c in retrieval["chunks"]
            ]
            rag_distances = [c.get("distance", 0) for c in retrieval["chunks"]]

        # ── Step 2: Select prompt template ──
        previous = self.memory.get_last_interaction(session_id)

        if is_general_question:
            weather_block = ""
            if weather_data:
                weather_block = "**CURRENT WEATHER CONDITIONS:**\n" + build_weather_section(weather_data)
            user_prompt = GENERAL_QUESTION_PROMPT.format(
                rag_context=rag_context if rag_context else "No relevant knowledge retrieved.",
                weather_section_block=weather_block,
                user_message=message,
            )
            prompt_type = "general_question"
        elif is_low_confidence:
            prompt_type = "low_confidence"
            user_prompt = format_prompt(
                template=LOW_CONFIDENCE_PROMPT, pest_name=pest_name or "Unknown",
                confidence=confidence or 0.0, crop=crop or "Unknown",
                category_id=category_id or -1, user_message=message,
                rag_context=rag_context, vlm_description=vlm_description,
                weather_data=weather_data,
                previous_pest_name=previous.get("pest_name") if previous else None,
                previous_confidence=previous.get("confidence") if previous else None,
            )
        elif previous and previous.get("pest_name"):
            prompt_type = "follow_up"
            user_prompt = format_prompt(
                template=FOLLOW_UP_PROMPT, pest_name=pest_name or "Unknown",
                confidence=confidence or 0.0, crop=crop or "Unknown",
                category_id=category_id or -1, user_message=message,
                rag_context=rag_context, vlm_description=vlm_description,
                weather_data=weather_data,
                previous_pest_name=previous.get("pest_name") if previous else None,
                previous_confidence=previous.get("confidence") if previous else None,
            )
        else:
            prompt_type = "high_confidence"
            user_prompt = format_prompt(
                template=HIGH_CONFIDENCE_PROMPT, pest_name=pest_name or "Unknown",
                confidence=confidence or 0.0, crop=crop or "Unknown",
                category_id=category_id or -1, user_message=message,
                rag_context=rag_context, vlm_description=vlm_description,
                weather_data=weather_data,
                previous_pest_name=previous.get("pest_name") if previous else None,
                previous_confidence=previous.get("confidence") if previous else None,
            )

        # ── Step 3: Add language instruction ──
        lang_instruction = ""
        if language and language != "English":
            lang_instruction = f"\n\nIMPORTANT: Respond entirely in {language}. All headers, text, and advice must be in {language}."

        system_with_lang = SYSTEM_PROMPT + lang_instruction

        # ── Step 4: Check cache ──
        cache_key = user_prompt[:500]
        cached = self.cache.get(cache_key)
        if cached and not self.memory.get_conversation(session_id):
            self.analytics.cache_hits += 1
            llm_response = cached
            self.llm.provider = "cache"
        else:
            self.analytics.cache_misses += 1
            # ── Step 5: Generate with multi-turn history ──
            conversation_history = self.memory.get_conversation(session_id)
            llm_response = self.llm.generate(system_with_lang, user_prompt, history=conversation_history[:-1])
            self.cache.put(cache_key, llm_response)

        # ── Step 6: Append disclaimer ──
        full_reply = llm_response + LEGAL_DISCLAIMER

        # ── Step 7: Weather warnings ──
        weather_warning = None
        if weather_data and not weather_data.get("safe_to_spray", True):
            alerts = weather_data.get("alerts", [])
            condition = weather_data.get("condition", "Unknown")
            weather_warning = (
                f"🌧️ WEATHER ALERT: {', '.join(alerts) if alerts else condition}. "
                f"Current conditions are NOT safe for pesticide application."
            )

        # ── Step 8: Quality scoring ──
        if rag_sources and rag_distances:
            avg_dist = sum(rag_distances) / len(rag_distances)
            if avg_dist < 0.8:
                rag_quality = "high"
            elif avg_dist < 1.2:
                rag_quality = "medium"
            else:
                rag_quality = "low"
        elif rag_sources:
            rag_quality = "medium"
        else:
            rag_quality = "none"

        # ── Step 9: Generate follow-up suggestions ──
        suggestions = self._generate_suggestions(pest_name, crop, prompt_type, message)

        # ── Step 10: Save to memory ──
        self.memory.add_interaction(session_id, {
            "message": message, "pest_name": pest_name,
            "confidence": confidence, "crop": crop, "prompt_type": prompt_type,
        })
        # Add assistant response to multi-turn conversation
        self.memory.add_message(session_id, "assistant", llm_response[:500])

        # ── Step 11: Record analytics ──
        elapsed = time.time() - t_start
        self.analytics.record(self.llm.provider or "unknown", prompt_type, elapsed)

        # Add relevance scores to sources
        enriched_sources = []
        for i, src in enumerate(rag_sources):
            dist = rag_distances[i] if i < len(rag_distances) else None
            relevance = max(0, min(100, int((1 - (dist or 1) / 2) * 100))) if dist is not None else None
            enriched_sources.append({**src, "relevance": relevance})

        return {
            "reply": full_reply,
            "disclaimer": LEGAL_DISCLAIMER,
            "is_low_confidence": is_low_confidence,
            "rag_sources": enriched_sources,
            "weather_warning": weather_warning,
            "session_id": session_id,
            "prompt_type": prompt_type,
            "llm_provider": self.llm.provider,
            "response_time": round(elapsed, 2),
            "rag_quality": rag_quality,
            "suggestions": suggestions,
            "provider_count": self.get_provider_count(),
        }

    def _generate_suggestions(self, pest_name, crop, prompt_type, message) -> list:
        """Generate context-aware follow-up suggestions."""
        if prompt_type == "low_confidence":
            return [
                "📸 How can I take a better photo for identification?",
                "🐛 What are common pests in my region?",
                "🌿 What are general IPM strategies?",
            ]
        if pest_name and pest_name not in ("Unknown", "Uncertain"):
            base = [
                f"🧪 What organic alternatives exist for {pest_name}?",
                f"⏰ When is the best time to treat {pest_name}?",
                f"🛡️ How to prevent {pest_name} in the future?",
            ]
            if crop and crop != "Unknown":
                base.append(f"🌾 What other pests affect {crop}?")
            return base[:3]
        return [
            "🐛 How to identify common crop pests?",
            "🌿 What is Integrated Pest Management (IPM)?",
            "🌧️ Is it safe to spray pesticides in rainy weather?",
        ]


# ============================================================================
# Quick test
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  Testing PestManagementAgent")
    print("=" * 60)

    agent = PestManagementAgent()
    print(f"\nActive providers: {agent.get_provider_count()}")

    # Test 1: High confidence
    print("\n--- TEST 1: High Confidence ---")
    result = agent.chat(
        message="How do I treat aphids on my rice field?",
        pest_name="Aphid", confidence=0.91, crop="Rice", session_id="test-1",
    )
    print(f"Type: {result['prompt_type']}")
    print(f"LLM: {result['llm_provider']}")
    print(f"Time: {result['response_time']}s")
    print(f"Quality: {result['rag_quality']}")
    print(f"Suggestions: {result['suggestions']}")
    print(f"Reply (first 200 chars): {result['reply'][:200]}...")

    # Test 2: Follow-up (same session)
    print("\n--- TEST 2: Follow-up (multi-turn) ---")
    result = agent.chat(
        message="Can you explain more about the organic options?",
        pest_name="Aphid", confidence=0.91, crop="Rice", session_id="test-1",
    )
    print(f"Type: {result['prompt_type']}")
    print(f"Reply (first 200 chars): {result['reply'][:200]}...")

    print(f"\n--- Analytics ---")
    print(agent.analytics.to_dict())
    print("\nAll tests completed!")
