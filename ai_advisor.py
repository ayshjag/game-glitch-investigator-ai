"""
AI Advisor: RAG-powered hint engine using Google Gemini.

Pipeline
--------
1. Retrieve relevant strategy tips from knowledge_base/ (RAG)
2. Build a structured prompt with game state + retrieved context
3. Call Gemini to generate a specific next-guess recommendation
4. Validate the suggestion is within the valid range (guardrail)
5. Compute a confidence score based on how much of the range is eliminated
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional

import google.generativeai as genai

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

KNOWLEDGE_BASE_DIR = Path(__file__).parent / "knowledge_base"
GEMINI_MODEL = "gemini-1.5-flash"


# ---------------------------------------------------------------------------
# RAG: retrieval from local knowledge base
# ---------------------------------------------------------------------------

def load_knowledge_base() -> dict[str, str]:
    """Load all .txt files from knowledge_base/ into a dict keyed by filename."""
    docs = {}
    if not KNOWLEDGE_BASE_DIR.exists():
        logger.warning("knowledge_base/ directory not found")
        return docs
    for path in sorted(KNOWLEDGE_BASE_DIR.glob("*.txt")):
        docs[path.stem] = path.read_text(encoding="utf-8").strip()
    logger.info("Loaded %d knowledge base documents", len(docs))
    return docs


def retrieve_relevant_tips(
    low: int,
    high: int,
    history: list[int],
    attempts_left: int,
    last_feedback: str,
) -> str:
    """
    Select the most relevant strategy tips based on current game state.
    Returns a combined string of retrieved context.
    """
    docs = load_knowledge_base()
    selected = []

    # Always include binary search — it's always relevant
    if "binary_search_strategy" in docs:
        selected.append(docs["binary_search_strategy"])

    # Include hot/cold strategy if there's feedback to act on
    if last_feedback in ("Hot", "Warm", "Cold") and "hot_cold_strategy" in docs:
        selected.append(docs["hot_cold_strategy"])

    # Include attempt management when attempts are limited
    if attempts_left <= 3 and "attempt_management" in docs:
        selected.append(docs["attempt_management"])

    return "\n\n---\n\n".join(selected)


# ---------------------------------------------------------------------------
# Confidence scoring (algorithmic, no API call needed)
# ---------------------------------------------------------------------------

def compute_confidence(low: int, high: int, original_range_size: int) -> float:
    """
    Return a 0.0–1.0 confidence score representing how much of the
    original range has been eliminated.

    confidence = 1 - (remaining / original)
    A fresh game returns 0.0; one number left returns ~1.0.
    """
    remaining = max(high - low + 1, 1)
    original = max(original_range_size, 1)
    confidence = 1.0 - (remaining / original)
    return round(min(max(confidence, 0.0), 1.0), 2)


# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------

def validate_hint(hint: int, low: int, high: int) -> tuple[bool, str]:
    """
    Confirm the AI-suggested hint is within the current valid range.
    Returns (is_valid, error_message).
    """
    if not isinstance(hint, int):
        return False, f"Hint must be an integer, got {type(hint).__name__}"
    if hint < low or hint > high:
        return False, f"Hint {hint} is outside the valid range [{low}, {high}]"
    return True, ""


def _extract_integer(text: str, low: int, high: int) -> int | None:
    """
    Parse the first integer from a string that falls within [low, high].
    Returns None if no valid integer is found.
    """
    import re
    for token in re.findall(r"-?\d+", text):
        value = int(token)
        if low <= value <= high:
            return value
    return None


# ---------------------------------------------------------------------------
# Main advisor
# ---------------------------------------------------------------------------

def get_ai_hint(
    api_key: str,
    low: int,
    high: int,
    history: list[int | str],
    attempts_left: int,
    last_feedback: str,
    original_range_size: int,
) -> dict:
    """
    Run the full RAG + Gemini agentic pipeline and return a hint dict.

    Returns
    -------
    {
        "hint": int | None,
        "explanation": str,
        "confidence": float,
        "strategy_used": str,
        "valid": bool,
        "error": str | None,
    }
    """
    result = {
        "hint": None,
        "explanation": "",
        "confidence": 0.0,
        "strategy_used": "",
        "valid": False,
        "error": None,
    }

    # --- Step 1: input guardrail ---
    if low > high:
        result["error"] = "Invalid range: low > high"
        logger.error("Invalid range: low=%d high=%d", low, high)
        return result

    # --- Step 2: compute confidence (no API needed) ---
    result["confidence"] = compute_confidence(low, high, original_range_size)

    # --- Step 3: RAG retrieval ---
    context = retrieve_relevant_tips(low, high, history, attempts_left, last_feedback)
    logger.info("RAG retrieved %d characters of context", len(context))

    # --- Step 4: build prompt ---
    history_str = ", ".join(str(g) for g in history) if history else "none yet"
    prompt = f"""You are an expert advisor for a number guessing game.

GAME STATE:
- Current valid range: [{low}, {high}]
- Guesses so far: {history_str}
- Attempts remaining: {attempts_left}
- Last feedback: {last_feedback if last_feedback else "none"}

STRATEGY KNOWLEDGE BASE:
{context}

TASK:
Based on the game state and strategy knowledge above, recommend the single best next guess.
Your response must follow this exact format:
GUESS: <integer between {low} and {high}>
STRATEGY: <one sentence naming the strategy used>
EXPLANATION: <one or two sentences explaining why this is the best guess>

Do not include any other text."""

    # --- Step 5: call Gemini ---
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(GEMINI_MODEL)
        logger.info("Calling Gemini API for hint (range [%d, %d])", low, high)
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        logger.info("Gemini raw response: %s", raw_text)
    except Exception as exc:
        result["error"] = f"Gemini API error: {exc}"
        logger.error("Gemini API error: %s", exc)
        # Fallback: pure binary search
        fallback = (low + high) // 2
        result["hint"] = fallback
        result["explanation"] = f"API unavailable — using binary search fallback: guess {fallback}"
        result["strategy_used"] = "Binary Search (fallback)"
        result["valid"] = True
        return result

    # --- Step 6: parse response ---
    hint_value = None
    strategy = ""
    explanation = ""

    for line in raw_text.splitlines():
        line = line.strip()
        if line.startswith("GUESS:"):
            raw_num = line.replace("GUESS:", "").strip()
            hint_value = _extract_integer(raw_num, low, high)
        elif line.startswith("STRATEGY:"):
            strategy = line.replace("STRATEGY:", "").strip()
        elif line.startswith("EXPLANATION:"):
            explanation = line.replace("EXPLANATION:", "").strip()

    # Fallback parse: scan full text if structured parse failed
    if hint_value is None:
        hint_value = _extract_integer(raw_text, low, high)
        logger.warning("Structured parse failed; extracted %s from full text", hint_value)

    if hint_value is None:
        hint_value = (low + high) // 2
        explanation = f"Could not parse AI response — using binary search midpoint: {hint_value}"
        strategy = "Binary Search (parse fallback)"
        logger.warning("Using midpoint fallback: %d", hint_value)

    # --- Step 7: output guardrail ---
    is_valid, err = validate_hint(hint_value, low, high)
    if not is_valid:
        hint_value = (low + high) // 2
        explanation = f"AI hint was out of range — corrected to midpoint: {hint_value}"
        strategy = "Binary Search (guardrail correction)"
        is_valid = True
        logger.warning("Guardrail triggered: corrected to %d", hint_value)

    result["hint"] = hint_value
    result["explanation"] = explanation
    result["strategy_used"] = strategy
    result["valid"] = is_valid
    return result
