
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
def expectiminimax_one_ply_with_cutoff2(state: GameState, top_k_ai=14, top_k_opp=10, verbose=False):
    assert state.dice, "AI dice must be set before calling expectiminimax."
    ai_sequences = state.generate_all_sequences_for_dice(AI, tuple(state.dice))
    if not ai_sequences:
        if verbose:
            print("AI: no legal sequences for rolled dice.")
        return []

    scored = []
    for seq in ai_sequences:
        st = state.clone()
        for m in seq:
            st.apply_move(m, AI)
        v = evaluate_state(st)
        scored.append((v, seq, st))
    scored.sort(key=lambda x: x[0])
    candidates = scored[:top_k_ai]
    if verbose:
        print(f"AI generated {len(ai_sequences)} sequences, keeping top {len(candidates)} candidates")

    opp_outcomes = unordered_dice_outcomes_with_weights()
    total_weight = sum(w for _, w in opp_outcomes)

    eval_cache = {}
    def eval_cached(st):
        key = (tuple(st.points), st.bear_off[PLAYER], st.bear_off[AI])
        if key in eval_cache:
            return eval_cache[key]
        val = evaluate_state(st)
        eval_cache[key] = val
        return val

    BMIN = -1_000_000.0
    best_seq = None
    best_expected = float("inf")

    for idx, (base_val, seq, st_after_ai) in enumerate(candidates):
        # if verbose:
        #     print(f"\nCandidate {idx+1}: immediate eval {base_val:.3f} (seq len {len(seq)})")
        if st_after_ai.bear_off[AI] >= 15:
            # if verbose:
            #     print(" Immediate AI win detected for this candidate; selecting it.")
            return seq

        partial_sum = 0.0
        processed_w = 0
        pruned = False

        for outcome, weight in opp_outcomes:
            opp_seqs = st_after_ai.generate_all_sequences_for_dice(PLAYER, outcome)
            if not opp_seqs:
                opp_best_val = eval_cached(st_after_ai)
            else:
                scored_opp = []
                for oseq in opp_seqs:
                    st2 = st_after_ai.clone()
                    for m in oseq:
                        st2.apply_move(m, PLAYER)
                    v2 = eval_cached(st2)
                    scored_opp.append((v2, oseq))
                scored_opp.sort(key=lambda x: x[0], reverse=True)
                opp_best_val = scored_opp[0][0]
            partial_sum += weight * opp_best_val
            processed_w += weight
            remaining_w = total_weight - processed_w

            optimistic_total = partial_sum + remaining_w * BMIN
            optimistic_expected = optimistic_total / total_weight

            # if verbose:
            #     print(f"  outcome {outcome} w={weight} -> opp_best={opp_best_val:.3f}, partial_sum={partial_sum:.3f}, optimistic_expected={optimistic_expected:.3f}, best_so_far={best_expected:.3f}")

            if optimistic_expected >= best_expected:
                pruned = True
                # if verbose:
                #     print("  -> Candidate pruned by optimistic bound (cutoff).")
                break

        if not pruned:
            expected_val = partial_sum / total_weight
            # if verbose:
            #     print(f" Candidate final expected value = {expected_val:.3f}")
            if expected_val < best_expected:
                best_expected = expected_val
                best_seq = seq
                # if verbose:
                #     print(f"  -> New best candidate (expected {best_expected:.3f})")

    if best_seq is None:
        # if verbose:
        #     print("All candidates pruned; falling back to first immediate-best candidate.")
        return candidates[0][1]
    return best_seq