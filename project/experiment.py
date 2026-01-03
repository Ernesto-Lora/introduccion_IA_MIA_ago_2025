import time
import random
from datetime import datetime
from collections import namedtuple

# --- Import your modules ---
from gameState import GameState 

# IMPORTS (Adjust names if your files are named differently)
# We assume these functions now accept (state, player_id, ...)
# OR we will wrap them below if they don't.
try:
    from csp_arc_consistency import expectiminimax_two_ply as ai1_logic
    from expectiminimax import expectiminimax_one_ply_with_cutoff2 as ai2_logic
except ImportError:
    print("Error: Could not import AI modules. Make sure files exist.")
    exit()

# Constants
PLAYER_1 = 1    # "White" / AI 1 (CSP)
PLAYER_2 = -1   # "Black" / AI 2 (Base)

# =============================================================================
# WRAPPER TO FIX THE "HARDCODED PLAYER" BUG
# =============================================================================
# Use this wrapper if your imported functions still use global AI = -1
# This forces the function to see the correct perspective.

def smart_ai_caller(ai_func, state, player_id, strategy_name):
    """
    Calls the AI function. If the AI function is hardcoded for Player -1,
    but we are Player 1, we might need to 'flip' the board view conceptually
    if the AI module doesn't support 'player_id' argument.
    
    HOWEVER, the best fix is to pass 'player_id' to the function.
    """
    try:
        # Try calling with player_id (The correct way)
        # Check your expectiminimax definitions! They MUST accept player_id.
        return ai_func(state, player_id=player_id, verbose=False)
    except TypeError:
        # Fallback: The function doesn't accept player_id. 
        # It likely uses global AI=-1.
        # This is DANGEROUS for Player 1. We must warn.
        if player_id == 1:
            print(f"WARNING: {strategy_name} might be hardcoded for Player -1!")
        return ai_func(state, verbose=False)

# =============================================================================
# MAIN EXPERIMENT
# =============================================================================
def run_experiment():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"game_experiment_{timestamp}.txt"
    print(f"Starting experiment. Logging to: {filename}")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Experiment Date: {timestamp}\n")
        f.write("Player 1 (White/Pos): CSP Arc Consistency (AI 1)\n")
        f.write("Player 2 (Black/Neg): Expectiminimax V2 (AI 2)\n")
        f.write("-" * 50 + "\n")

        state = GameState()
        state.setup_standard()
        
        # Ensure correct turn start
        current_player = PLAYER_1 
        state.current_player = current_player
        
        turn_count = 1
        max_turns = 200             # Reduced from 1000 (Game should end by turn 60-100)
        consecutive_passes = 0
        game_over = False
        winner = None

        while not game_over and turn_count < max_turns:
            # 1. Roll Dice
            d1 = random.randint(1, 6)
            d2 = random.randint(1, 6)
            
            # Setup dice in state
            if d1 == d2:
                state.dice = (d1, d1, d1, d1) # 4 dice for doubles
            else:
                state.dice = (d1, d2)
            
            # IMPORTANT: Ensure state knows whose turn it is
            state.current_player = current_player

            player_label = "AI 1 (CSP)" if current_player == PLAYER_1 else "AI 2 (Base)"
            log_header = f"Turn {turn_count}: {player_label} | Dice: {state.dice}"
            print(log_header)
            f.write(log_header + "\n")

            # 2. AI Thinking
            start_time = time.time()
            
            best_sequence = []
            
            # CALLING THE AI WITH PLAYER ID
            if current_player == PLAYER_1:
                # Assuming ai1_logic is updated to: def func(state, player_id, ...)
                best_sequence = ai1_logic(state, player_id=PLAYER_1) 
            else:
                # Assuming ai2_logic is updated to: def func(state, player_id, ...)
                best_sequence = ai2_logic(state, player_id=PLAYER_2)

            elapsed = time.time() - start_time
            f.write(f"    Time: {elapsed:.4f}s\n")

            # 3. Execute Moves
            if best_sequence:
                consecutive_passes = 0
                moves_log = []
                
                # Apply moves one by one
                for move in best_sequence:
                    # VALIDATION: Check if move is legal before applying?
                    # Trusting the AI for now, but in rigorous experiments, validate here.
                    state.apply_move(move, current_player)
                    moves_log.append(f"{move.from_pt}->{move.to_pt}")
                
                f.write(f"    Moves: {', '.join(moves_log)}\n")
            else:
                consecutive_passes += 1
                f.write("    Moves: PASS (No legal moves or AI failed)\n")
                print(f"    -> PASSED")

            # 4. Check Win Condition
            # Bear off count usually goes to 15
            if state.bear_off[PLAYER_1] == 15:
                winner = "AI 1 (CSP)"
                game_over = True
            elif state.bear_off[PLAYER_2] == 15:
                winner = "AI 2 (Base)"
                game_over = True
            
            # 5. Deadlock / Stalemate Check
            if consecutive_passes >= 6: # 3 turns each with no moves
                print("DEADLOCK: 6 Consecutive passes.")
                winner = "DRAW (Stalemate)"
                game_over = True

            # Switch Turn
            current_player = -current_player
            state.current_player = current_player
            state.dice = () # Clear dice
            turn_count += 1
            f.write("\n")

        # Result
        if not winner: winner = "DRAW (Turn Limit)"
        
        final_msg = f"\n{'='*30}\nFINAL RESULT: {winner}\nTotal Turns: {turn_count}\n{'='*30}"
        print(final_msg)
        f.write(final_msg)

if __name__ == "__main__":
    run_experiment()