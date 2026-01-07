
## Create the virtual environment

From the project root directory, run:

```bash
python3 -m venv .venv
```

This will create a `.venv` folder containing the isolated environment.

---

##  Activate the virtual environment

### macOS / Linux

```bash
source .venv/bin/activate
```

When activated, your terminal prompt should look similar to:

```
(.venv) user@machine:~/project$
```

---

## Upgrade `pip` (recommended)

```bash
pip install --upgrade pip
```

---

## Install project dependencies

```bash
pip install -r requirements.txt
```


---

## Environment successfully configured

You can now run the project inside the virtual environment.


## How to Play

Run the following commands to play a game against the AI.

**Play against the Baseline AI (Expectiminimax)**

```bash
python3 backgmn_eminimax.py

```

**Play against the Improved AI (CSP/Arc Consistency)**

```bash
python3 backgmn_improvement.py

```

---

## Testing & Debugging

These scripts demonstrate specific scenarios to verify game logic and highlight bugs in the baseline version compared to the fixed improvement version.

### Baseline Bugs

* **`baseline_test.py`**
* **Scenario:** Forces the first roll to be a pair of 6s.
* **Identified Bug:** The player is able to move checkers arbitrarily from the board (ignoring legal move constraints).


* **`baseline_test2.py`**
* **Scenario:** Sets up a predefined board structure where the player has no legal moves.
* **Identified Bug:** The baseline implementation fails to pass the turn when no moves are available.



### Improvement Fixes

These scripts run the same scenarios as above but verify that the bugs have been resolved in the improved version.

* **`improvement_test1.py`**: verifies the fix for the arbitrary move bug.
* **`improvement_test2.py`**: verifies the fix for the "no legal moves" turn-passing logic.

---

## Experiments

Run automated simulations between the Baseline AI and the Improved CSP AI.

**Experiment 1: CSP moves first**
Runs a single game where the CSP AI takes the first turn against the Baseline.

```bash
python3 experiment.py

```

* **Output:** Generates a log file in the `games/` folder containing the move history, the winner, and the average thinking time.

**Experiment 2: Baseline moves first**
Runs the same simulation, but the Baseline AI takes the first turn.

```bash
python3 experiment2.py

```

---
