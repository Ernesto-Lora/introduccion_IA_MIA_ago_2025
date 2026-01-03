
import pygame
import sys
import random
from collections import namedtuple
from csp_arc_consistency import BackgammonCSP

# ---- Config / UI constants ----
WIDTH, HEIGHT = 900, 520
BOARD_X = 40
BOARD_Y = 40
POINT_W = 36
POINT_H = 160
GAP = 8
FPS = 30

# Colors (user-specified)
BG = (8, 80, 44)              # deep green felt
WOOD = (60, 30, 12)           # dark brown wood outer frame
TRI_A = (145, 182, 216)       # light blue
TRI_B = (255, 140, 0)         # bright orange
IVORY = (248, 244, 227)       # ivory (player)
BLACK = (25, 25, 25)          # black (AI)
HIGHLIGHT = (180, 50, 50)     # selection circle
LEGAL_MARKER = (30, 200, 90)  # legal destination marker
TEXT_COLOR = (255, 255, 55)   # general on-board text color
STRIKE_COLOR = (0, 0, 0)      # stroke color for numbers (black)

# Game constants
NUM_POINTS = 24
PLAYER = 1
AI = -1
Move = namedtuple("Move", ["from_pt", "to_pt", "die_used"])
# to_pt == NUM_POINTS => player bear-off; to_pt == -1 => ai bear-off

from gameState import GameState

# ---- Heuristic evaluation ----
def evaluate_state(state: GameState):
    borne_diff = state.bear_off[PLAYER] - state.bear_off[AI]
    pip_diff = state.pip_count(AI) - state.pip_count(PLAYER)
    pieces_player = sum(x for x in state.points if x > 0)
    pieces_ai = sum(-x for x in state.points if x < 0)
    score = 30.0 * borne_diff + 0.05 * pip_diff + 0.2 * (pieces_player - pieces_ai)
    return float(score)

# ---- Unordered dice combos (21) with weights ----
def unordered_dice_outcomes_with_weights():
    combos = []
    for d1 in range(1, 7):
        for d2 in range(d1, 7):
            weight = 1 if d1 == d2 else 2
            combos.append(((d1, d2), weight))
    return combos

# ---- Expectiminimax (one decision ply) ----
def expectiminimax_one_ply_with_cutoff2(state: GameState, player_id: int, top_k_ai=14, top_k_opp=10, verbose=False):
    assert state.dice, "AI dice must be set before calling expectiminimax."
    
    opponent_id = -player_id
    
    # 1. Generate Moves for Self
    ai_sequences = state.generate_all_sequences_for_dice(player_id, tuple(state.dice))
    if not ai_sequences:
        if verbose: print("AI: no legal sequences for rolled dice.")
        return []

    # 2. Score Candidates (Depth 0)
    scored = []
    for seq in ai_sequences:
        st = state.clone()
        for m in seq:
            st.apply_move(m, player_id)
        
        raw_v = evaluate_state(st)
        # Flip score if we are Player -1 so that "Higher is Better" always holds
        v = raw_v if player_id == 1 else -raw_v
        
        scored.append((v, seq, st))
    
    # Sort Highest Score First (Best moves for us)
    scored.sort(key=lambda x: x[0], reverse=True)
    candidates = scored[:top_k_ai]
    
    if verbose:
        print(f"AI generated {len(ai_sequences)} sequences, keeping top {len(candidates)} candidates")

    opp_outcomes = unordered_dice_outcomes_with_weights()
    total_weight = sum(w for _, w in opp_outcomes)

    eval_cache = {}
    def eval_cached(st):
        key = (tuple(st.points), st.bear_off[player_id], st.bear_off[opponent_id])
        if key in eval_cache: return eval_cache[key]
        
        raw_v = evaluate_state(st)
        # Store perspective-adjusted score
        val = raw_v if player_id == 1 else -raw_v
        eval_cache[key] = val
        return val

    # We want to MAXIMIZE our expected value. 
    # Current best is -infinity.
    best_seq = None
    best_expected = -float("inf")
    
    # Alpha-Beta style bound? 
    # In Expectiminimax with Star pruning, we usually track an Alpha bound.
    # Here we stick to simple expectation maximization.

    for idx, (base_val, seq, st_after_ai) in enumerate(candidates):
        
        # Immediate Win Check
        if st_after_ai.bear_off[player_id] >= 15:
            return seq

        partial_sum = 0.0
        
        for outcome, weight in opp_outcomes:
            opp_seqs = st_after_ai.generate_all_sequences_for_dice(opponent_id, outcome)
            
            if not opp_seqs:
                opp_best_val = eval_cached(st_after_ai)
            else:
                scored_opp = []
                for oseq in opp_seqs:
                    st2 = st_after_ai.clone()
                    for m in oseq:
                        st2.apply_move(m, opponent_id)
                    
                    v2 = eval_cached(st2)
                    scored_opp.append(v2)
                
                # Opponent minimizes OUR score
                opp_best_val = min(scored_opp)
                
            partial_sum += weight * opp_best_val

        expected_val = partial_sum / total_weight
        
        if expected_val > best_expected:
            best_expected = expected_val
            best_seq = seq

    if best_seq is None:
        return candidates[0][1]
        
    return best_seq