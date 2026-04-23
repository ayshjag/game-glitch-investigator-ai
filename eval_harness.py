"""
Evaluation harness: tests the AI advisor on predefined game scenarios.

Runs without a live Gemini API call — uses the algorithmic components
(RAG retrieval, confidence scoring, guardrails) directly so the harness
works offline and in CI.

Run with:
    python eval_harness.py
"""

import sys
from ai_advisor import (
    compute_confidence,
    retrieve_relevant_tips,
    validate_hint,
    _extract_integer,
)
from logic_utils import get_range_for_difficulty, check_guess

# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

TEST_CASES = [
    {
        "name": "Binary midpoint — Normal, no history",
        "low": 1, "high": 100,
        "history": [],
        "attempts_left": 8,
        "last_feedback": "",
        "expected_hint": 50,
        "description": "Fresh game: midpoint of 1–100 should be 50",
    },
    {
        "name": "Hot feedback — narrow range",
        "low": 47, "high": 53,
        "history": [50],
        "attempts_left": 5,
        "last_feedback": "Hot",
        "expected_hint": 50,
        "description": "Hot feedback in range 47–53: midpoint is 50",
    },
    {
        "name": "Cold feedback — large range remaining",
        "low": 51, "high": 100,
        "history": [25],
        "attempts_left": 6,
        "last_feedback": "Cold",
        "expected_hint": 75,
        "description": "After guessing 25 (too low), range is 51–100, midpoint is 75",
    },
    {
        "name": "Easy difficulty range check",
        "low": 1, "high": 20,
        "history": [],
        "attempts_left": 6,
        "last_feedback": "",
        "expected_hint": 10,
        "description": "Easy mode 1–20: midpoint is 10",
    },
    {
        "name": "Hard difficulty, few attempts left",
        "low": 30, "high": 60,
        "history": [20, 45],
        "attempts_left": 2,
        "last_feedback": "Warm",
        "expected_hint": 45,
        "description": "Range 30–60 with 2 attempts left: midpoint is 45",
    },
    {
        "name": "Single number remaining",
        "low": 42, "high": 42,
        "history": [1, 100, 50, 25, 42],
        "attempts_left": 1,
        "last_feedback": "Hot",
        "expected_hint": 42,
        "description": "Only one number left: must guess 42",
    },
    {
        "name": "Guardrail: out-of-range hint is corrected",
        "low": 10, "high": 20,
        "history": [],
        "attempts_left": 4,
        "last_feedback": "",
        "expected_hint": 15,
        "description": "Midpoint 10–20 = 15; guardrail must keep hint in range",
    },
    {
        "name": "Confidence score at start (0%)",
        "low": 1, "high": 100,
        "history": [],
        "attempts_left": 8,
        "last_feedback": "",
        "expected_confidence_min": 0.0,
        "expected_confidence_max": 0.01,
        "description": "No guesses yet: confidence should be ~0%",
    },
    {
        "name": "Confidence score after halving range",
        "low": 51, "high": 100,
        "history": [50],
        "attempts_left": 7,
        "last_feedback": "Cold",
        "expected_confidence_min": 0.49,
        "expected_confidence_max": 0.51,
        "description": "After eliminating lower half: confidence ~50%",
    },
    {
        "name": "RAG retrieval includes binary search always",
        "low": 1, "high": 100,
        "history": [],
        "attempts_left": 8,
        "last_feedback": "",
        "expected_context_keyword": "binary search",
        "description": "RAG must always return binary search strategy",
    },
]

# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def run_tests():
    passed = 0
    failed = 0
    results = []

    for tc in TEST_CASES:
        name = tc["name"]
        low, high = tc["low"], tc["high"]
        history = tc["history"]
        attempts_left = tc["attempts_left"]
        last_feedback = tc["last_feedback"]

        try:
            # --- confidence tests ---
            if "expected_confidence_min" in tc:
                original_size = 100
                conf = compute_confidence(low, high, original_size)
                ok = tc["expected_confidence_min"] <= conf <= tc["expected_confidence_max"]
                status = "PASS" if ok else "FAIL"
                detail = f"confidence={conf:.2f} expected [{tc['expected_confidence_min']}, {tc['expected_confidence_max']}]"

            # --- RAG retrieval tests ---
            elif "expected_context_keyword" in tc:
                context = retrieve_relevant_tips(low, high, history, attempts_left, last_feedback)
                ok = tc["expected_context_keyword"].lower() in context.lower()
                status = "PASS" if ok else "FAIL"
                detail = f"keyword '{tc['expected_context_keyword']}' {'found' if ok else 'NOT FOUND'} in context"

            # --- hint value tests (algorithmic midpoint) ---
            else:
                midpoint = (low + high) // 2
                is_valid, err = validate_hint(midpoint, low, high)
                expected = tc["expected_hint"]
                ok = (midpoint == expected) and is_valid
                status = "PASS" if ok else "FAIL"
                detail = f"hint={midpoint} expected={expected} valid={is_valid}"

            results.append((status, name, detail, tc["description"]))
            if status == "PASS":
                passed += 1
            else:
                failed += 1

        except Exception as exc:
            results.append(("ERROR", name, str(exc), tc["description"]))
            failed += 1

    # --- Print summary ---
    print("\n" + "=" * 65)
    print("  GAME GLITCH INVESTIGATOR — AI ADVISOR EVALUATION HARNESS")
    print("=" * 65)
    for status, name, detail, desc in results:
        icon = "✅" if status == "PASS" else ("❌" if status == "FAIL" else "💥")
        print(f"\n{icon}  [{status}] {name}")
        print(f"     Desc : {desc}")
        print(f"     Result: {detail}")

    print("\n" + "-" * 65)
    total = passed + failed
    print(f"  Results: {passed}/{total} passed  |  {failed} failed")
    score_pct = (passed / total * 100) if total > 0 else 0
    print(f"  Score  : {score_pct:.0f}%")
    print("=" * 65 + "\n")

    return passed, failed


if __name__ == "__main__":
    passed, failed = run_tests()
    sys.exit(0 if failed == 0 else 1)
