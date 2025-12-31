from collections import deque
from gameState import GameState

from collections import deque, namedtuple


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

# Ensure these are available if not already imported in your file
# from gameState import GameState
# Move = namedtuple("Move", ["from_pt", "to_pt", "die_used"])


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

class BackgammonCSP:
    """
    Implements a Constraint Satisfaction Problem (CSP) using the AC-3 algorithm.
    
    Variables: The dice available to be played (e.g., Die 0, Die 1).
    Domains: The set of legal single moves available for each die.
    Constraints: A move for Die X is consistent with Die Y if, after playing X,
                 there is at least one valid move available for Die Y.
                 (This enforces the 'maximize dice usage' rule).
    """
    def __init__(self, state: GameState, dice: tuple, player_id: int):
        self.state = state
        self.dice = dice
        self.player = player_id
        # We treat each die index as a variable (0 to len(dice)-1)
        self.variables = list(range(len(dice)))
        self.domains = {}
        self._initialize_domains()

    def _initialize_domains(self):
        """
        Populate initial domains by asking the GameState for all legal 
        sequences of length 1 for each individual die.
        """
        for var_idx in self.variables:
            die_val = self.dice[var_idx]
            # Get legal moves for strictly this single die value
            # Note: We pass the die as a single-element tuple (die_val,)
            seqs = self.state.generate_all_sequences_for_dice(self.player, (die_val,))
            
            # Flatten sequences: seqs is [[Move], [Move]], we want {Move, Move}
            # We use a set to avoid duplicates and allow fast lookup
            valid_moves = set()
            if seqs:
                for seq in seqs:
                    if seq: # Ensure sequence is not empty
                        valid_moves.add(seq[0])
            
            self.domains[var_idx] = list(valid_moves)

    def is_consistent(self, move_x, var_y_idx):
        """
        Check Arc Consistency: X -> Y
        If we commit to 'move_x' for Variable X, is there ANY valid move 
        left for Variable Y (Die Y)?
        """
        die_val_y = self.dice[var_y_idx]
        
        # 1. Simulate the state after move_x
        # We must clone efficiently.
        next_state = self.state.clone()
        next_state.apply_move(move_x, self.player)
        
        # 2. Check if Die Y has any legal moves in this new state
        possible_next_moves = next_state.generate_all_sequences_for_dice(
            self.player, (die_val_y,)
        )
        
        # If the list is not empty, there is at least one valid move for Y
        return len(possible_next_moves) > 0

    def revise(self, xi, xj):
        """
        Removes values from Domain[xi] that make Domain[xj] empty.
        Returns True if Domain[xi] was modified.
        """
        revised = False
        domain_xi = self.domains[xi]
        
        # We iterate over a copy of the list so we can remove items safely
        for x_val in list(domain_xi):
            # Check if this specific move x_val allows ANY move for die xj
            if not self.is_consistent(x_val, xj):
                # If playing x_val makes die xj unusable, we prune x_val
                # (Strict enforcement of "must use both dice if possible")
                domain_xi.remove(x_val)
                revised = True
                
        return revised

    def run_ac3(self):
        """
        The main AC-3 loop.
        """
        queue = deque()
        
        # Initialize queue with all directed arcs between distinct dice
        for i in self.variables:
            for j in self.variables:
                if i != j:
                    queue.append((i, j))
        
        while queue:
            (xi, xj) = queue.popleft()
            
            if self.revise(xi, xj):
                # If a domain becomes empty, it implies we can't use all dice
                # starting with the remaining moves. In a strict CSP this is failure.
                # In Backgammon, it usually means we are forced to play fewer dice.
                if not self.domains[xi]:
                    return self.domains 
                
                # If we pruned Xi, we must re-check neighbors pointing to Xi
                for xk in self.variables:
                    if xk != xi and xk != xj:
                        queue.append((xk, xi))
                        
        return self.domains


def expectiminimax_one_ply_with_cutoff(state: GameState, top_k_ai=14, top_k_opp=10, verbose=False):
    """
    Modified Expectiminimax with CSP Arc Consistency (AC-3) pruning.
    """
    assert state.dice, "AI dice must be set before calling expectiminimax."
    
    # ---------------------------------------------------------
    # 1. CSP / AC-3 Pruning Phase
    # ---------------------------------------------------------
    # Only run CSP if we have at least 2 dice to check consistency between.
    valid_start_moves = None
    
    if len(state.dice) >= 2:
        # Initialize the CSP solver
        csp = BackgammonCSP(state, state.dice, AI)
        
        # Run AC-3 to prune domains
        pruned_domains = csp.run_ac3()
        
        # Collect all "consistent" first moves across all dice variables
        # This set represents all moves that are guaranteed NOT to block the remaining dice
        valid_start_moves = set()
        for var_idx, moves in pruned_domains.items():
            for m in moves:
                valid_start_moves.add(m)
        
        if verbose:
            print(f"[CSP] AC-3 identified {len(valid_start_moves)} arc-consistent starting moves.")

    # ---------------------------------------------------------
    # 2. Sequence Generation (Filtered)
    # ---------------------------------------------------------
    # Generate all standard sequences
    ai_sequences = state.generate_all_sequences_for_dice(AI, tuple(state.dice))
    
    if not ai_sequences:
        if verbose:
            print("AI: no legal sequences for rolled dice.")
        return []

    # If CSP found valid moves, filter the sequences.
    # We only keep sequences that start with a move identified as consistent.
    if valid_start_moves is not None and len(valid_start_moves) > 0:
        filtered_sequences = []
        for seq in ai_sequences:
            if not seq: continue
            # Check if the first move of the sequence is in our allowed CSP set
            if seq[0] in valid_start_moves:
                filtered_sequences.append(seq)
        
        # If filtering left us with nothing (edge case), revert to original
        # This handles cases where we are forced to play only 1 die but CSP tried to enforce 2.
        if filtered_sequences:
            if verbose:
                print(f"[CSP] Pruned sequences from {len(ai_sequences)} to {len(filtered_sequences)}")
            ai_sequences = filtered_sequences

    # ---------------------------------------------------------
    # 3. Standard Expectiminimax Logic
    # ---------------------------------------------------------
    scored = []
    for seq in ai_sequences:
        st = state.clone()
        for m in seq:
            st.apply_move(m, AI)
        v = evaluate_state(st)
        scored.append((v, seq, st))
    
    # Sort by heuristic evaluation
    scored.sort(key=lambda x: x[0])
    
    # Keep top K candidates
    candidates = scored[:top_k_ai]
    if verbose:
        print(f"AI keeping top {len(candidates)} candidates for detailed search.")

    # Prepare opponent outcomes
    opp_outcomes = unordered_dice_outcomes_with_weights()
    total_weight = sum(w for _, w in opp_outcomes)

    # Cache for opponent evaluations
    eval_cache = {}
    def eval_cached(st):
        # Create a hashable key for the state configuration
        key = (tuple(st.points), st.bear_off[PLAYER], st.bear_off[AI])
        if key in eval_cache:
            return eval_cache[key]
        val = evaluate_state(st)
        eval_cache[key] = val
        return val

    BMIN = -1_000_000.0
    best_seq = None
    best_expected = float("inf")

    # Evaluate candidates with Expectimax
    for idx, (base_val, seq, st_after_ai) in enumerate(candidates):
        
        # Immediate win check
        if st_after_ai.bear_off[AI] >= 15:
            return seq

        partial_sum = 0.0
        processed_w = 0
        pruned = False

        for outcome, weight in opp_outcomes:
            # Generate opponent responses
            opp_seqs = st_after_ai.generate_all_sequences_for_dice(PLAYER, outcome)
            
            if not opp_seqs:
                # Opponent has no moves
                opp_best_val = eval_cached(st_after_ai)
            else:
                # 1-ply max for opponent
                scored_opp = []
                for oseq in opp_seqs:
                    st2 = st_after_ai.clone()
                    for m in oseq:
                        st2.apply_move(m, PLAYER)
                    v2 = eval_cached(st2)
                    scored_opp.append((v2, oseq))
                
                # Opponent maximizes their score
                scored_opp.sort(key=lambda x: x[0], reverse=True)
                opp_best_val = scored_opp[0][0]

            partial_sum += weight * opp_best_val
            processed_w += weight
            remaining_w = total_weight - processed_w

            # Optimistic pruning (Star1/Star2 logic)
            # Assuming best case for remaining outcomes is BMIN (terrible for opp, good for AI)
            optimistic_total = partial_sum + remaining_w * BMIN
            optimistic_expected = optimistic_total / total_weight

            if optimistic_expected >= best_expected:
                pruned = True
                break

        if not pruned:
            expected_val = partial_sum / total_weight
            if expected_val < best_expected:
                best_expected = expected_val
                best_seq = seq

    if best_seq is None:
        return candidates[0][1]
        
    return best_seq