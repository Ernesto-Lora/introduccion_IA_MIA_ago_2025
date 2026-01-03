import time
import random
from datetime import datetime
from collections import namedtuple

# Ensure this matches the definition expected by your GameState and AI modules
Move = namedtuple("Move", ["from_pt", "to_pt", "die_used"])

# --- Import your modules ---
# Assuming gameState.py is in the same folder
from gameState import GameState 

# AI 1: Arc Consistency Approach
from csp_arc_consistency import expectiminimax_two_ply as ai1_move_function

# AI 2: Expectiminimax Approach
from expectiminimax import expectiminimax_one_ply_with_cutoff2 as ai2_move_function

# Constants
AI_1 = 1   # Acts as "Player 1" (formerly the human player slot)
AI_2 = -1  # Acts as "AI" (formerly the AI slot)

def run_experiment():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"game{timestamp}.txt"
    print(f"Starting experiment. Logging to: {filename}")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Experiment Date: {timestamp}\n")
        f.write("AI 1 (Player 1): csp_arc_consistency\n")
        f.write("AI 2 (Player -1): expectiminimax (v2)\n")
        f.write("-" * 40 + "\n")

        state = GameState()
        state.setup_standard()
        current_player = AI_1 
        turn_count = 1
        
        # --- NEW: Counters for safety ---
        max_turns = 1000            # Hard limit just in case
        consecutive_passes = 0      # Track how many times in a row NO ONE moved
        game_over = False
        winner = None

        while not game_over and turn_count < max_turns:
            # 1. Roll Dice
            d1 = random.randint(1, 6)
            d2 = random.randint(1, 6)
            if d1 == d2:
                state.dice = (d1, d1)
                state.dice_left = [d1] * 4
            else:
                state.dice = (d1, d2)
                state.dice_left = [d1, d2]
            
            player_name = "AI 1" if current_player == AI_1 else "AI 2"
            log_header = f"Turn {turn_count}: {player_name} (Dice: {state.dice})"
            # print(log_header) # Optional: comment out to reduce console spam
            f.write(log_header + "\n")

            # 2. AI Thinking
            start_time = time.time()
            if current_player == AI_1:
                best_sequence = ai1_move_function(state, verbose=False)
            else:
                best_sequence = ai2_move_function(state, top_k_ai=20, top_k_opp=10, verbose=False)
            elapsed = time.time() - start_time
            
            f.write(f"    Time: {elapsed:.5f}s\n")

            # 3. Execute Moves and Check for Pass
            if best_sequence:
                consecutive_passes = 0  # RESET counter because someone moved
                moves_str = []
                for move in best_sequence:
                    state.apply_move(move, current_player)
                    moves_str.append(f"({move.from_pt}->{move.to_pt})")
                f.write(f"    Moves: {', '.join(moves_str)}\n")
            else:
                consecutive_passes += 1 # INCREMENT counter
                f.write("    Moves: NO LEGAL MOVES\n")
                print(f"Turn {turn_count}: {player_name} has NO LEGAL MOVES")

            # 4. Check Win Condition
            if state.bear_off[AI_1] >= 15:
                winner = "AI 1"
                game_over = True
            elif state.bear_off[AI_2] >= 15:
                winner = "AI 2"
                game_over = True
            
            # 5. Check Deadlock (New Feature)
            # If 10 turns happen in a row where NOBODY moves (5 turns each), stop.
            if consecutive_passes >= 10:
                print(f"DEADLOCK DETECTED at Turn {turn_count}. Stopping.")
                f.write("\n*** DEADLOCK DETECTED (10 consecutive passes) ***\n")
                winner = "DRAW (Stalemate)"
                game_over = True

            # Switch Turn
            current_player = -current_player
            state.current_player = current_player
            state.dice = ()
            state.dice_left = []
            turn_count += 1
            f.write("\n")

        # End of Game Summary
        result_msg = "-" * 40 + f"\nGAME OVER\nResult: {winner}\nTotal Turns: {turn_count}"
        if turn_count >= max_turns:
            result_msg += " (Hit Max Turn Limit)"
            
        print(result_msg)
        f.write(result_msg + "\n")

if __name__ == "__main__":
    run_experiment()