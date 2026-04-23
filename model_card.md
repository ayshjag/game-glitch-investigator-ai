# Model Card — Game Glitch Investigator AI Advisor

## Model Details

| Field | Value |
|---|---|
| Model used | Google Gemini 1.5 Flash |
| Provider | Google AI Studio (free tier) |
| Integration | `google-generativeai` Python SDK |
| Task | Game strategy advisor — recommend optimal next guess in a number guessing game |
| Input | Game state: current range, guess history, attempts left, hot/cold feedback |
| Output | Structured: GUESS (integer), STRATEGY (one sentence), EXPLANATION (one–two sentences) |

---

## System Limitations and Biases

- **Numeric range**: The model is prompted to stay within `[low, high]`, but it can occasionally hallucinate a number outside the range. The output guardrail in `ai_advisor.py` detects and corrects this automatically.
- **Over-explanation**: On trivially simple states (e.g. range of 1), Gemini sometimes adds unnecessary reasoning. The structured parser ignores extra text.
- **Python version**: The system runs on Python 3.8. The `google-generativeai` SDK raises `FutureWarning` for Python < 3.10. Functionality is unaffected but upgrading Python is recommended.
- **No learning across games**: The advisor has no memory of previous game sessions. Each call is stateless — it only knows the current game state.
- **English only**: The knowledge base and prompts are in English. Non-English inputs are not supported.

---

## Potential Misuse and Prevention

| Risk | Mitigation |
|---|---|
| Using the AI advisor to trivially auto-win every game | The advisor gives guidance, not a guaranteed answer — Gemini can mis-estimate, and the player still types the guess manually |
| Prompt injection via the guess history field | History is formatted as a comma-separated integer list; non-integer entries are rejected by `parse_guess()` before they reach the advisor |
| API key exposure | The key is entered in a Streamlit password field and read from `GEMINI_API_KEY` env var; it is never written to disk or logged |

---

## Testing Results

```
python eval_harness.py

Results: 10/10 passed  |  0 failed  |  Score: 100%
```

**Surprising findings:**
- Confidence scoring is fully deterministic and does not require an API call — it is purely algorithmic (`1 - remaining/original`), which makes it fast and reliable.
- The guardrail (Step 6) was never triggered during manual testing with valid API responses, suggesting Gemini 1.5 Flash reliably respects the range constraint when prompted explicitly.
- Fallback to binary search midpoint on API error means the system degrades gracefully — players always get a hint even if the internet is down.

---

## AI Collaboration During Development

**Helpful suggestion:** Claude Code suggested using a structured prompt format (`GUESS: / STRATEGY: / EXPLANATION:`) instead of asking for free-form text. This made response parsing simple and reliable without needing JSON mode.

**Flawed suggestion:** Claude Code initially generated type hints using Python 3.10+ syntax (`dict[str, str]`, `int | None`) which caused a `TypeError` on this project's Python 3.8 environment. The fix was to add `from __future__ import annotations` at the top of `ai_advisor.py`.

---

## Future Improvements

- Upgrade to Python 3.11+ to fully support the latest Gemini SDK features.
- Add a game history log so the advisor can learn patterns across sessions.
- Extend the knowledge base with difficulty-specific strategies (e.g. Hard mode with only 5 attempts).
- Add a "confidence threshold" guardrail: if Gemini returns a low-confidence response, automatically fall back to binary search.
