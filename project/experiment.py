import time
import random
from datetime import datetime
from collections import namedtuple

# --- Import your modules ---
from gameState import GameState 

# IMPORTS (Adjust names if your files are named differently)
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
# MAIN EXPERIMENT
# =============================================================================
def run_experiment():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"games/game_experiment_{timestamp}.txt"
    print(f"Starting experiment. Logging to: {filename}")
    
    # --- STATISTICS TRACKING ---
    stats = {
        PLAYER_1: {'total_time': 0.0, 'moves_count': 0, 'name': "AI 1 (CSP)"},
        PLAYER_2: {'total_time': 0.0, 'moves_count': 0, 'name': "AI 2 (Base)"}
    }

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Experiment Date: {timestamp}\n")
        f.write("Player 1 (White/Pos): CSP Arc Consistency (AI 1)\n")
        f.write("Player 2 (Black/Neg): Expectiminimax V2 (AI 2)\n")
        f.write("-" * 50 + "\n")

        state = GameState()
        state.setup_standard()
        
        current_player = PLAYER_1 
        state.current_player = current_player
        
        turn_count = 1
        max_turns = 200             
        consecutive_passes = 0
        game_over = False
        winner = None

        while not game_over and turn_count < max_turns:
            # 1. Roll Dice
            d1 = random.randint(1, 6)
            d2 = random.randint(1, 6)
            
            if d1 == d2:
                state.dice = (d1, d1, d1, d1) 
            else:
                state.dice = (d1, d2)
            
            state.current_player = current_player

            player_label = stats[current_player]['name']
            log_header = f"Turn {turn_count}: {player_label} | Dice: {state.dice}"
            print(log_header)
            f.write(log_header + "\n")

            # 2. AI Thinking
            start_time = time.time()
            
            best_sequence = []
            
            if current_player == PLAYER_1:
                best_sequence = ai1_logic(state, player_id=PLAYER_1) 
            else:
                best_sequence = ai2_logic(state, player_id=PLAYER_2)

            elapsed = time.time() - start_time
            f.write(f"    Time: {elapsed:.4f}s\n")

            # --- UPDATE STATS ---
            stats[current_player]['total_time'] += elapsed
            stats[current_player]['moves_count'] += 1

            # 3. Execute Moves
            if best_sequence:
                consecutive_passes = 0
                moves_log = []
                
                for move in best_sequence:
                    state.apply_move(move, current_player)
                    moves_log.append(f"{move.from_pt}->{move.to_pt}")
                
                f.write(f"    Moves: {', '.join(moves_log)}\n")
            else:
                consecutive_passes += 1
                f.write("    Moves: PASS (No legal moves or AI failed)\n")
                print(f"    -> PASSED")

            # 4. Check Win Condition
            if state.bear_off[PLAYER_1] == 15:
                winner = stats[PLAYER_1]['name']
                game_over = True
            elif state.bear_off[PLAYER_2] == 15:
                winner = stats[PLAYER_2]['name']
                game_over = True
            
            # 5. Deadlock / Stalemate Check
            if consecutive_passes >= 6: 
                print("DEADLOCK: 6 Consecutive passes.")
                winner = "DRAW (Stalemate)"
                game_over = True

            # Switch Turn
            current_player = -current_player
            state.current_player = current_player
            state.dice = () 
            turn_count += 1
            f.write("\n")

        # Result
        if not winner: winner = "DRAW (Turn Limit)"
        
        # --- CALCULATE AVERAGES ---
        final_msg = [
            f"\n{'='*30}",
            f"FINAL RESULT: {winner}",
            f"Total Turns: {turn_count}",
            f"{'-'*30}",
            "PERFORMANCE STATISTICS:",
        ]

        # Calculate for both players
        for pid in [PLAYER_1, PLAYER_2]:
            p_stats = stats[pid]
            if p_stats['moves_count'] > 0:
                avg_time = p_stats['total_time'] / p_stats['moves_count']
            else:
                avg_time = 0.0
            
            stat_line = (f"{p_stats['name']} -> "
                         f"Avg Time: {avg_time:.4f}s | "
                         f"Total Time: {p_stats['total_time']:.2f}s | "
                         f"Moves: {p_stats['moves_count']}")
            final_msg.append(stat_line)

        final_msg.append(f"{'='*30}")
        final_text = "\n".join(final_msg)

        print(final_text)
        f.write(final_text)

if __name__ == "__main__":
    run_experiment()