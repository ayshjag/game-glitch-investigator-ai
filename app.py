import os
import random
import streamlit as st

from logic_utils import (
    check_guess,
    get_range_for_difficulty,
    parse_guess,
    update_score,
)
from ai_advisor import get_ai_hint

HIGH_SCORE_FILE = "high_score.txt"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


def load_high_score():
    if not os.path.exists(HIGH_SCORE_FILE):
        return 0
    try:
        with open(HIGH_SCORE_FILE, "r", encoding="utf-8") as f:
            value = int(f.read().strip() or 0)
            return max(value, 0)
    except Exception:
        return 0


def save_high_score(score: int):
    try:
        with open(HIGH_SCORE_FILE, "w", encoding="utf-8") as f:
            f.write(str(score))
    except Exception:
        pass


st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-powered guessing game with a strategy advisor.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")
st.sidebar.caption(f"High Score: {st.session_state.get('high_score', 0)}")

st.sidebar.divider()
st.sidebar.subheader("AI Advisor")
api_key_input = st.sidebar.text_input(
    "Gemini API Key",
    value=GEMINI_API_KEY,
    type="password",
    help="Enter your Google Gemini API key to enable the AI hint advisor.",
)


def reset_game_state(low_value, high_value):
    st.session_state.attempts = 0
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []
    st.session_state.secret = random.randint(low_value, high_value)
    st.session_state.current_low = low_value
    st.session_state.current_high = high_value
    st.session_state.last_feedback = ""
    st.session_state.ai_hint = None


if "difficulty" not in st.session_state:
    st.session_state.difficulty = difficulty

if "high_score" not in st.session_state:
    st.session_state.high_score = load_high_score()

if "secret" not in st.session_state:
    reset_game_state(low, high)

if st.session_state.difficulty != difficulty:
    st.session_state.difficulty = difficulty
    reset_game_state(low, high)

if "current_low" not in st.session_state:
    st.session_state.current_low = low
if "current_high" not in st.session_state:
    st.session_state.current_high = high
if "last_feedback" not in st.session_state:
    st.session_state.last_feedback = ""
if "ai_hint" not in st.session_state:
    st.session_state.ai_hint = None

st.subheader("Make a guess")

st.info(
    f"Guess a number between {low} and {high}. "
    f"Attempts left: {max(attempt_limit - st.session_state.attempts, 0)}"
)

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)
    st.write("Narrowed range:", st.session_state.current_low, "–", st.session_state.current_high)

raw_guess = st.text_input("Enter your guess:", key=f"guess_input_{difficulty}")

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

if new_game:
    reset_game_state(low, high)
    st.success("New game started.")
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    st.stop()

if submit:
    st.session_state.attempts += 1
    st.session_state.ai_hint = None

    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        st.session_state.history.append(raw_guess)
        st.error(err)
    else:
        st.session_state.history.append(guess_int)

        outcome, message = check_guess(guess_int, st.session_state.secret)

        if show_hint:
            if outcome == "Too High":
                st.error(message)
            elif outcome == "Too Low":
                st.info(message)
            elif outcome == "Win":
                st.success(message)
            else:
                st.warning(message)

        if outcome in ["Too High", "Too Low"]:
            distance = abs(guess_int - st.session_state.secret)
            if distance <= 3:
                feedback = "Hot"
                st.success("🔥 Hot! You are very close.")
            elif distance <= 10:
                feedback = "Warm"
                st.info("🌶️ Warm. Keep going.")
            else:
                feedback = "Cold"
                st.write("❄️ Cold. Try a bigger adjustment.")
            st.session_state.last_feedback = feedback

            if outcome == "Too High":
                st.session_state.current_high = guess_int - 1
            else:
                st.session_state.current_low = guess_int + 1

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        st.table(
            {
                "Metric": ["Attempts", "Score", "High Score", "Secret"],
                "Value": [
                    st.session_state.attempts,
                    st.session_state.score,
                    st.session_state.high_score,
                    st.session_state.secret if st.session_state.status != "playing" else "?",
                ],
            }
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            if st.session_state.score > st.session_state.high_score:
                st.session_state.high_score = st.session_state.score
                save_high_score(st.session_state.high_score)
                st.success("🎉 New high score! Saved to disk.")
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score} "
                f"(High score: {st.session_state.high_score})"
            )
        else:
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error(
                    f"Out of attempts! "
                    f"The secret was {st.session_state.secret}. "
                    f"Score: {st.session_state.score}"
                )

# ---------------------------------------------------------------------------
# AI Advisor Panel
# ---------------------------------------------------------------------------
st.divider()
st.subheader("🤖 AI Strategy Advisor")

if st.session_state.status != "playing":
    st.info("Start a new game to use the AI advisor.")
elif not api_key_input:
    st.warning("Enter your Gemini API key in the sidebar to enable AI hints.")
else:
    original_range_size = high - low + 1
    attempts_left = attempt_limit - st.session_state.attempts

    col_hint, col_conf = st.columns([3, 1])
    with col_hint:
        ask_ai = st.button("Ask AI for best next guess 🧠")
    with col_conf:
        if st.session_state.ai_hint:
            conf = st.session_state.ai_hint.get("confidence", 0.0)
            st.metric("Confidence", f"{conf * 100:.0f}%")

    if ask_ai:
        with st.spinner("AI is analysing the game state..."):
            hint_result = get_ai_hint(
                api_key=api_key_input,
                low=st.session_state.current_low,
                high=st.session_state.current_high,
                history=st.session_state.history,
                attempts_left=attempts_left,
                last_feedback=st.session_state.last_feedback,
                original_range_size=original_range_size,
            )
        st.session_state.ai_hint = hint_result

    if st.session_state.ai_hint:
        hint_result = st.session_state.ai_hint

        if hint_result.get("error") and hint_result["hint"] is None:
            st.error(f"AI Advisor error: {hint_result['error']}")
        else:
            if hint_result.get("error"):
                st.warning(f"Note: {hint_result['error']}")

            st.success(f"**AI recommends: {hint_result['hint']}**")

            if hint_result.get("strategy_used"):
                st.caption(f"Strategy: {hint_result['strategy_used']}")

            if hint_result.get("explanation"):
                st.write(hint_result["explanation"])

            conf = hint_result.get("confidence", 0.0)
            st.progress(conf, text=f"Search confidence: {conf * 100:.0f}% of range eliminated")

st.divider()
st.caption("Built with Google Gemini AI — strategy powered by RAG knowledge base.")
