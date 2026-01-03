from collections import deque, namedtuple
from gameState import GameState 

# ---- Constants ----
# (Ensure these match your existing setup)
PLAYER = 1
AI = -1

# =============================================================================
# 1. PRO-LEVEL HEURISTIC EVALUATION
# =============================================================================
def evaluate_state(state: GameState):
    """
    Dynamic Heuristic: Adapts strategy based on Game Phase.
    """
    # --- 0. Win/Loss (Absolute) ---
    if state.bear_off[AI] == 15: return 1_000_000.0
    if state.bear_off[PLAYER] == 15: return -1_000_000.0

    # --- 1. Detect Game Phase (Contact vs. Race) ---
    # Contact is broken if the most advanced PLAYER checker has passed 
    # the furthest back AI checker.
    
    # Find furthest back checker indices (0-23)
    # AI moves -1 to -24. Its furthest back is the highest index with negative count.
    # PLAYER moves 1 to 24. Its furthest back is lowest index with positive count.
    
    player_furthest_back = -1
    ai_furthest_back = -1
    
    for i in range(24):
        if state.points[i] > 0 and player_furthest_back == -1:
            player_furthest_back = i
        if state.points[i] < 0:
            ai_furthest_back = i
            
    # In standard representation:
    # Player moves 0->23. AI moves 23->0 (conceptually). 
    # Actually, your board likely uses specific indices. 
    # Let's assume standard logic: If all Player pieces > all AI pieces indices?
    # NO. If AI moves NEGATIVE (24->1) and Player moves POSITIVE (1->24).
    # "Contact Broken" means AI's highest index < Player's lowest index.
    
    is_race_phase = False
    if ai_furthest_back < player_furthest_back:
        is_race_phase = True

    score = 0.0
    
    # --- HYPERPARAMETERS ---
    # Tweak these to change personality
    K_PIP = 2.0         # Value of 1 pip in race
    K_HIT = 1000.0      # Value of hitting opponent
    K_BLOT = 250.0      # Penalty for being vulnerable
    K_PRIME = 80.0      # Bonus for 3+ block wall
    K_ANCHOR = 150.0    # Bonus for holding opponent 5-pt
    K_BEAROFF = 500.0   # Bonus per piece borne off

    # --- 2. Evaluation Logic ---

    # A. RACE SCORE (Pips)
    pips_ai = state.pip_count(AI)
    pips_player = state.pip_count(PLAYER)
    
    if is_race_phase:
        # PURE RACE MODE: Only speed matters!
        # Significantly amplify pip importance.
        score -= (pips_ai - pips_player) * 10.0
        
        # Massive bonus for bearing off
        score += state.bear_off[AI] * 1000.0
        
        # Zero penalty for blots (safely ignore them)
        return float(score)

    # B. CONTACT MODE (Standard Game)
    
    # 1. Base Pip Score (Less important than structure)
    score -= (pips_ai - pips_player) * K_PIP

    # 2. Hitting (Crucial)
    score += state.bar[PLAYER] * K_HIT
    score -= state.bar[AI] * K_HIT

    # 3. Structure & Safety
    consecutive_ai = 0
    
    for i in range(24):
        count = state.points[i]
        
        # AI Piece
        if count < 0:
            if count == -1:
                # BLOT PENALTY
                # Heavily penalize blots in our home board (0-5)
                # Less penalty if opponent is on bar (can't hit us easily)
                risk_factor = 1.0
                if state.bar[PLAYER] > 0: risk_factor = 0.2 # Safe to be loose if opp is on bar
                
                if i <= 5: score -= (K_BLOT * 1.5) * risk_factor
                else:      score -= K_BLOT * risk_factor
                
                consecutive_ai = 0
            else:
                # Block/Prime Building
                consecutive_ai += 1
                if consecutive_ai >= 3:
                    score += K_PRIME * consecutive_ai # Escalating bonus for long primes
        else:
            consecutive_ai = 0

    # 4. Strategic Anchors (Holding opponent's home)
    # Opponent home is 19-23 (indices). 
    # AI holding index 19, 20, 21 is very strong.
    for i in [19, 20, 21]: 
        if state.points[i] <= -2:
            score += K_ANCHOR

    # 5. Bear-off (Even in contact, good to bank checkers)
    score += state.bear_off[AI] * K_BEAROFF

    return float(score)

# =============================================================================
# 2. CSP / ARC CONSISTENCY (Required & Optimized)
# =============================================================================
class BackgammonCSP:
    def __init__(self, state: GameState, dice: tuple, player_id: int):
        self.state = state
        self.dice = dice
        self.player = player_id
        self.variables = list(range(len(dice)))
        self.domains = {}
        self._initialize_domains()

    def _initialize_domains(self):
        # Find moves legal for each specific die individually
        for var_idx in self.variables:
            die_val = self.dice[var_idx]
            seqs = self.state.generate_all_sequences_for_dice(self.player, (die_val,))
            valid_moves = set()
            if seqs:
                for seq in seqs:
                    if seq: valid_moves.add(seq[0])
            self.domains[var_idx] = list(valid_moves)

    def is_consistent(self, move_x, var_y_idx):
        die_val_y = self.dice[var_y_idx]
        next_state = self.state.clone()
        next_state.apply_move(move_x, self.player)
        possible_next_moves = next_state.generate_all_sequences_for_dice(self.player, (die_val_y,))
        return len(possible_next_moves) > 0

    def revise(self, xi, xj):
        revised = False
        domain_xi = self.domains[xi]
        for x_val in list(domain_xi):
            if not self.is_consistent(x_val, xj):
                domain_xi.remove(x_val)
                revised = True
        return revised

    def run_ac3(self):
        queue = deque()
        for i in self.variables:
            for j in self.variables:
                if i != j: queue.append((i, j))
        
        while queue:
            (xi, xj) = queue.popleft()
            if self.revise(xi, xj):
                if not self.domains[xi]: return self.domains
                for xk in self.variables:
                    if xk != xi and xk != xj: queue.append((xk, xi))
        return self.domains

# =============================================================================
# 3. EXPECTIMINIMAX SEARCH
# =============================================================================
def unordered_dice_outcomes_with_weights():
    combos = []
    for d1 in range(1, 7):
        for d2 in range(d1, 7):
            weight = 1 if d1 == d2 else 2
            combos.append(((d1, d2), weight))
    return combos

# -------------------------------------------------------------------------
# HELPER: Dice Weights
# -------------------------------------------------------------------------
def unordered_dice_outcomes_with_weights():
    """Returns list of ((d1, d2), weight) for all 21 dice rolls."""
    combos = []
    for d1 in range(1, 7):
        for d2 in range(d1, 7):
            weight = 1 if d1 == d2 else 2
            combos.append(((d1, d2), weight))
    return combos

# -------------------------------------------------------------------------
# EVALUATION CACHE (To speed up 2-ply)
# -------------------------------------------------------------------------
# We use a global cache to avoid recalculating the score of the same board twice
transposition_table = {}

def get_eval(state):
    """Checks cache, otherwise calculates evaluate_state."""
    # Create a unique key for the board configuration
    key = (tuple(state.points), state.bear_off[PLAYER], state.bear_off[AI], 
           state.bar[PLAYER], state.bar[AI])
    
    if key in transposition_table:
        return transposition_table[key]
    
    val = evaluate_state(state)
    transposition_table[key] = val
    return val

# -------------------------------------------------------------------------
# 2-PLY EXPECTIMINIMAX WITH BEAM SEARCH
# -------------------------------------------------------------------------
def expectiminimax_two_ply(state: GameState, player_id: int, verbose=False):
    """
    Performs a Depth-2 Search:
    Root (Self) -> Chance -> Opponent -> Chance -> Self -> Static Eval
    """
    assert state.dice, "AI dice must be set."
    
    # Identify opponent dynamically
    opponent_id = -player_id
    
    # Clear cache at start of turn (assuming transposition_table is global)
    transposition_table.clear() 

    # --- PHASE 1: CSP FILTER (ROOT ONLY) ---
    valid_start_moves = None
    if len(state.dice) >= 2:
        try:
            # Pass correct player_id to CSP
            csp = BackgammonCSP(state, state.dice, player_id)
            pruned = csp.run_ac3()
            valid_start_moves = {m for moves in pruned.values() for m in moves}
        except: pass

    # --- PHASE 2: ROOT MOVES (SELF) ---
    # Generate moves for the SPECIFIC player_id passed to the function
    root_moves = state.generate_all_sequences_for_dice(player_id, tuple(state.dice))
    if not root_moves: return []

    # Apply CSP Filter
    if valid_start_moves:
        filtered = [s for s in root_moves if s and s[0] in valid_start_moves]
        if filtered: root_moves = filtered

    # BEAM SEARCH PRUNING:
    candidates = []
    for seq in root_moves:
        st = state.clone()
        for m in seq: st.apply_move(m, player_id)
        
        # Evaluate from the perspective of the current player_id
        # Note: We assume evaluate_state returns a high positive score 
        # for 'player_id' winning. If evaluate_state is absolute (Positive=Player 1),
        # we might need to flip the sign here.
        # SAFE APPROACH: Pass player_id to evaluate_state if supported, 
        # or flip manually if needed. 
        # Assuming standard evaluate_state (Positive = Player 1, Negative = Player -1):
        raw_score = evaluate_state(st)
        score = raw_score if player_id == 1 else -raw_score
        
        candidates.append((score, seq, st))
    
    # Sort best to worst and keep Top 4
    candidates.sort(key=lambda x: x[0], reverse=True)
    beam_candidates = candidates[:4] 

    if verbose: print(f"2-Ply: Searching top {len(beam_candidates)} candidate moves...")

    # --- PHASE 3: DEEP SEARCH ---
    best_seq = None
    best_value = -float("inf")
    
    outcomes = unordered_dice_outcomes_with_weights()
    total_weight = sum(w for _, w in outcomes)

    for base_score, seq, st_after_root in beam_candidates:
        
        # Win check optimization
        if st_after_root.bear_off[player_id] == 15: return seq

        weighted_score_sum = 0.0
        
        for dice_opp, w_opp in outcomes:
            
            # --- OPPONENT LAYER (Min Node) ---
            # Opponent plays their best move
            opp_moves = st_after_root.generate_all_sequences_for_dice(opponent_id, dice_opp)
            
            if not opp_moves:
                # If opponent cannot move, current board stands.
                raw_v = get_eval(st_after_root)
                val_opp = raw_v if player_id == 1 else -raw_v
            else:
                # Opponent wants to MINIMIZE our score (Maximize theirs)
                # From our perspective, this is a Min node.
                worst_outcome_for_us = float("inf")
                
                # Check opponent moves (Limit to 5 for speed)
                limit_opp = 5 if len(opp_moves) > 5 else len(opp_moves)
                
                for oseq in opp_moves[:limit_opp]: # Simple slice for speed
                    st_opp = st_after_root.clone()
                    for m in oseq: st_opp.apply_move(m, opponent_id)
                    
                    raw_v = get_eval(st_opp)
                    # Convert to our perspective
                    v_perspective = raw_v if player_id == 1 else -raw_v
                    
                    if v_perspective < worst_outcome_for_us:
                        worst_outcome_for_us = v_perspective
                
                val_opp = worst_outcome_for_us

            weighted_score_sum += val_opp * w_opp

        expected_val = weighted_score_sum / total_weight
        
        if expected_val > best_value:
            best_value = expected_val
            best_seq = seq
            
    return best_seq if best_seq else candidates[0][1]