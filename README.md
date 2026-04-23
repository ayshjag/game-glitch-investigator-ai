# 🎮 Game Glitch Investigator — Applied AI System

> **Base project:** [AI110 Module 1 — Game Glitch Investigator](https://github.com/ayshjag/ai110-module1show-gameglitchinvestigator-starter)
> The original project was a Streamlit number-guessing game where players debugged a broken AI-generated game. It featured difficulty levels, hot/cold feedback, a scoring system, and a high-score tracker. Bugs in session state, type handling, and hint logic were identified and fixed as the core learning exercise.

---

## What This Project Does

This extended version transforms the guessing game into a full **applied AI system** by adding:

- A **RAG-powered AI Strategy Advisor** that retrieves guessing strategies from a local knowledge base and uses Google Gemini to recommend the optimal next guess.
- An **agentic pipeline** with observable steps: input validation → RAG retrieval → prompt construction → Gemini inference → output guardrail → confidence scoring.
- An **offline evaluation harness** (`eval_harness.py`) that runs 10 predefined test scenarios and prints a pass/fail summary.

---

## System Architecture

```
Player Input (Streamlit UI)
        │
        ▼
  logic_utils.py ──► parse / check / score
        │
        ▼
  Range Narrowing ──► current_low / current_high updated after each guess
        │
  [Ask AI Button]
        │
        ▼
  ai_advisor.py  (Agentic Pipeline)
    Step 1 │ Input Guardrail    — reject invalid ranges
    Step 2 │ RAG Retrieval      — load relevant tips from knowledge_base/
    Step 3 │ Prompt Building    — game state + retrieved context
    Step 4 │ Gemini API         — generate GUESS / STRATEGY / EXPLANATION
    Step 5 │ Response Parsing   — structured extraction
    Step 6 │ Output Guardrail   — clamp hint to valid range
           │
           ▼
    Hint + Confidence Score displayed to player

  eval_harness.py (offline)
    10 test cases → confidence / RAG / guardrail checks → PASS/FAIL summary
```

See [assets/architecture.md](assets/architecture.md) for the full Mermaid diagram.

---

## Setup Instructions

### 1. Clone the repo
```bash
git clone https://github.com/ayshjag/game-glitch-investigator-ai.git
cd game-glitch-investigator-ai
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Get a free Gemini API key
Go to [aistudio.google.com](https://aistudio.google.com), sign in with Google, and create a free API key.

### 4. Run the app
```bash
streamlit run app.py
```
Enter your Gemini API key in the sidebar under **AI Advisor**. Play the game, then click **Ask AI for best next guess** to activate the advisor.

### 5. Run the evaluation harness (no API key needed)
```bash
python eval_harness.py
```

---

## Sample Interactions

### Example 1 — Fresh game (Normal, 1–100)
**Player asks AI at the start.**
```
AI recommends: 50
Strategy: Binary Search — guess the midpoint
Explanation: With range [1, 100] and no prior guesses, the midpoint 50 eliminates
             half the search space regardless of the outcome.
Search confidence: 0% of range eliminated
```

### Example 2 — After one "Too High" guess of 50 (range now 1–49)
```
AI recommends: 25
Strategy: Binary Search — continue halving
Explanation: Range is now [1, 49]. Guessing 25 eliminates another 50% of the
             remaining space. With 7 attempts left this is optimal.
Search confidence: 51% of range eliminated
```

### Example 3 — Hot feedback, range 47–53, 2 attempts left
```
AI recommends: 50
Strategy: Hot/Cold + Attempt Management — stay close, minimize moves
Explanation: You are hot (within 3 of the secret). With only 2 attempts left,
             the midpoint 50 is the safest single guess covering the center.
Search confidence: 94% of range eliminated
```

---

## Design Decisions

| Decision | Rationale |
|---|---|
| Google Gemini (free tier) | No cost barrier; accessible to all learners |
| Local RAG knowledge base (.txt files) | No vector DB needed; lightweight and auditable |
| Algorithmic confidence scoring | Deterministic and testable; no LLM call needed |
| Structured prompt with `GUESS:` / `STRATEGY:` / `EXPLANATION:` fields | Reliable parsing without JSON mode |
| Fallback to binary search midpoint | Ensures hint is always provided even on API error |
| Offline eval harness | Tests run in CI without API key; validates logic independently |

---

## Testing Summary

```
$ python eval_harness.py

Results: 10/10 passed  |  0 failed
Score  : 100%
```

**What was tested:**
- Binary search midpoint correctness across all difficulty ranges
- Hot/Cold/Cold feedback scenarios
- Single-number-remaining edge case
- Confidence score at 0% (fresh game) and ~50% (after halving range)
- RAG always retrieves binary search strategy
- Guardrail corrects any out-of-range AI hint

**What the AI struggled with:**
- On very small ranges (1–3 numbers), Gemini sometimes explains unnecessarily; the structured parser handles this gracefully.
- Python 3.8 requires `from __future__ import annotations` for modern type hint syntax.

---

## Reflection

This project taught me that a reliable AI system is built in layers: the LLM is just one step in a pipeline that needs guardrails before and after it. The confidence score and fallback logic mean the advisor is always helpful even when the API is unavailable.

**AI collaboration:** Claude Code helped design the agentic pipeline structure and the RAG retrieval logic. One helpful suggestion was using a structured `GUESS: / STRATEGY: / EXPLANATION:` prompt format to make parsing reliable. One flawed suggestion was using Python 3.10+ type hint syntax (`dict[str, str]`) which broke on this project's Python 3.8 environment.

---

## Demo

![Game Demo](final_game.gif)

> 📹 Loom walkthrough: *[add your Loom link here]*
