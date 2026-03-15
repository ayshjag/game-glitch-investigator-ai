# 🎮 Game Glitch Investigator: The Impossible Guesser

## 🚨 The Situation

You asked an AI to build a simple "Number Guessing Game" using Streamlit.
It wrote the code, ran away, and now the game is unplayable. 

- You can't win.
- The hints lie to you.
- The secret number seems to have commitment issues.

## 🛠️ Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run the broken app: `python -m streamlit run app.py`

## 🕵️‍♂️ Your Mission

1. **Play the game.** Open the "Developer Debug Info" tab in the app to see the secret number. Try to win.
2. **Find the State Bug.** Why does the secret number change every time you click "Submit"? Ask ChatGPT: *"How do I keep a variable from resetting in Streamlit when I click a button?"*
3. **Fix the Logic.** The hints ("Higher/Lower") are wrong. Fix them.
4. **Refactor & Test.** - Move the logic into `logic_utils.py`.
   - Run `pytest` in your terminal.
   - Keep fixing until all tests pass!

## 📝 Document Your Experience

This game is a Streamlit number guessing game where players try to guess a secret number within a given range and limited attempts. The original version had state and type bugs that caused the secret number to change unexpectedly and generated misleading hints. I moved critical logic into `logic_utils.py`, normalized guesses and secrets to integers in `check_guess`, fixed scoring in `update_score`, stabilized Streamlit session state, and added comprehensive unit tests in `tests/test_game_logic.py`.

## 📸 Demo

- Fixed game is playable and winning works correctly.
- Added a High Score tracker feature saved to `high_score.txt` and shown in the sidebar.
- Documented and fixed difficulty-switch bug: changing difficulty now resets game state and secret number properly.
- Added enhanced UI: color-coded hints, hot/cold emojis, and a player session summary table.
- Test output:


```
$ pytest -q
21 passed
```

- Screenshot of enhanced UI (paste image link or path):
  ![Game UI](screenshots/game_ui.png)

## Agent Contribution
- This feature expansion was planned and implemented with Copilot (agent mode) guidance: I asked for a meaningful new feature and then added high-score load/save logic in `app.py`, with comments noting agent collaboration.

## 🚀 Stretch Features
  [x] challenge 1:
  

- [x] challenge 4:

