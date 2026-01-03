from collections import deque, namedtuple
from gameState import GameState 

# ---- Constants ----
# (Ensure these match your existing setup)
PLAYER = 1
AI = -1

from collections import deque
import math

# Constants (adjust / tune)
PLAYER = 1
AI = -1

# ---------------------------
# Helper: unordered dice outcomes (21 combos)
# ---------------------------
def unordered_dice_outcomes_with_weights():
    combos = []
    for d1 in range(1, 7):
        for d2 in range(d1, 7):
            weight = 1 if d1 == d2 else 2
            combos.append(((d1, d2), weight))
    return combos

# ---------------------------
# 1) Cleaner evaluate_state (perspective-aware)
# ---------------------------
def evaluate_state(state: GameState, perspective: int = AI):
    """
    Returns a score where positive is good for `perspective` (PLAYER=1 or AI=-1).
    Uses pip counts, blots, primes, anchors, bars, and bearing off.
    """
    # Immediate wins/losses (absolute)
    if state.bear_off.get(perspective, 0) == 15:
        return 1_000_000.0
    if state.bear_off.get(-perspective, 0) == 15:
        return -1_000_000.0

    # Hyperparameters (tweakable)
    K_PIP = 2.0         # pip importance (baseline)
    K_PIP_RACE = 10.0   # pip importance during race
    K_HIT = 900.0       # value per opponent-on-bar (we hit them)
    K_BLOT = 220.0      # penalty for vulnerable singletons
    K_PRIME = 75.0      # prime bonus multiplier
    K_ANCHOR = 140.0    # anchor bonus
    K_BEAROFF = 450.0   # per borne-off checker
    K_HOME_STRENGTH = 45.0  # how much we value a strong home board

    # convenience
    opponent = -perspective
    points = state.points  # length 24, positive for PLAYER, negative for AI

    # Pip counts (lower is better). We want positive => advantage for perspective:
    my_pip = state.pip_count(perspective)
    opp_pip = state.pip_count(opponent)
    pip_diff = opp_pip - my_pip  # positive => good for perspective

    # Determine home indices depending on perspective orientation:
    # Assumption: PLAYER (1) moves from 0->23, home is 18..23; AI (-1) moves 23->0, home 0..5.
    if perspective == PLAYER:
        home_idx = list(range(18, 24))
        opp_home_idx = list(range(0, 6))
    else:
        home_idx = list(range(0, 6))
        opp_home_idx = list(range(18, 24))

    # count checkers in home
    my_home_checkers = sum(abs(points[i]) for i in home_idx if (points[i] * perspective) > 0)
    opp_home_checkers = sum(abs(points[i]) for i in opp_home_idx if (points[i] * opponent) > 0)

    # Race detection (simple heuristic): if many checkers are in home and pip diff matters
    is_race = False
    if (my_home_checkers >= 12 and opp_home_checkers >= 12) or abs(pip_diff) > 35:
        is_race = True

    score = 0.0

    # Race mode: primarily concerned with pip count and bearing off
    if is_race:
        score += pip_diff * K_PIP_RACE
        score += state.bear_off.get(perspective, 0) * K_BEAROFF
        # slight reward for safe home (less blots)
        # penalize number of blots in our home less aggressively in race
        blots_home = sum(1 for i in home_idx if (points[i] * perspective) == (1 * perspective))
        score -= blots_home * (K_BLOT * 0.6)
        return float(score)

    # Contact mode: structure matters
    # 1. Base pip contribution
    score += pip_diff * K_PIP

    # 2. Hits / bar (opponent's bar is good for us)
    # state.bar[opp] == number of opponent checkers on bar => good for perspective
    hits_for_us = state.bar[opponent]
    hits_against_us = state.bar[perspective]
    score += (hits_for_us - hits_against_us) * K_HIT

    # 3. Bear off
    score += state.bear_off.get(perspective, 0) * K_BEAROFF
    score -= state.bear_off.get(opponent, 0) * (K_BEAROFF * 0.5)  # opponent's borne-off helps them

    # 4. Primes and blots scanning
    consecutive = 0
    max_prime = 0
    home_blocks = 0
    blots_total = 0

    for i in range(24):
        cnt = points[i]
        if cnt * perspective > 0:
            # this point belongs to perspective
            if abs(cnt) == 1:
                blots_total += 1
                consecutive = 0
            else:
                # multi-checker point contributes to primes/consecutive
                consecutive += 1
                max_prime = max(max_prime, consecutive)
                if i in home_idx and abs(cnt) >= 2:
                    home_blocks += 1
        else:
            consecutive = 0

    score += max_prime * K_PRIME
    score -= blots_total * K_BLOT
    score += home_blocks * K_HOME_STRENGTH

    # 5. Strategic anchors: hold opponent's outer home points (strong defensive anchors)
    # Example: take a few important anchor indices near opponent home for each orientation
    if perspective == PLAYER:
        # check points 19..21 (defensive anchors in the opponent's inner board)
        anchor_idxs = [19, 20, 21]
    else:
        anchor_idxs = [4, 5, 6]  # approximate mirror indexes for AI
    for idx in anchor_idxs:
        if 0 <= idx < 24 and (points[idx] * perspective) <= -2:  # careful: presence of enemy pieces here?
            # If the opponent actually holds these (we want to hold opposite set) - don't over-penalize; skip ambiguous indexing
            pass

    # Slight adjustment to prefer stable positions when opponent has checkers on bar
    if state.bar[opponent] > 0:
        score += 40.0

    return float(score)


# ---------------------------
# 2) Transposition table / caching (perspective-aware)
# ---------------------------
transposition_table = {}
def get_eval(state: GameState, perspective: int):
    """
    Keyed by full board tuple and perspective.
    """
    # create a stable key
    key = (tuple(state.points),
           state.bear_off.get(PLAYER, 0), state.bear_off.get(AI, 0),
           state.bar.get(PLAYER, 0) if isinstance(state.bar, dict) else state.bar[PLAYER],
           state.bar.get(AI, 0) if isinstance(state.bar, dict) else state.bar[AI],
           perspective)
    if key in transposition_table:
        return transposition_table[key]
    val = evaluate_state(state, perspective)
    transposition_table[key] = val
    return val

# ---------------------------
# 3) Improved 2-ply expectiminimax with beam & opponent move ordering
# ---------------------------
def expectiminimax_two_ply(state: GameState, player_id: int, beam_width: int = 6, opp_move_limit: int = 6, verbose=False):
    """
    Depth-2 from a given rolled dice (state.dice must be set).
    Assumes evaluate_state returns positive for the supplied perspective.
    beam_width: how many candidate root moves to consider
    opp_move_limit: how many top opponent replies to consider per dice outcome
    """
    assert state.dice, "state.dice must be set to the current roll at root."

    opponent_id = -player_id
    transposition_table.clear()

    # 1) CSP pruning (optional) - keep as before but try to keep full sequences if possible
    valid_start_moves = None
    try:
        csp = BackgammonCSP(state, state.dice, player_id)
        pruned = csp.run_ac3()
        # build set of legal "first moves" that survived AC-3
        valid_start_moves = {m for moves in pruned.values() for m in moves}
    except Exception:
        valid_start_moves = None

    # 2) root move generation (for the rolled dice)
    root_moves = state.generate_all_sequences_for_dice(player_id, tuple(state.dice))
    if not root_moves:
        return []  # no moves

    # apply optional CSP filter (match by first move element if your sequences are lists of atomic moves)
    if valid_start_moves:
        filtered = [s for s in root_moves if s and s[0] in valid_start_moves]
        if filtered:
            root_moves = filtered

    # 3) produce beam candidates by static eval after applying each root seq
    candidates = []
    for seq in root_moves:
        st = state.clone()
        for m in seq:
            st.apply_move(m, player_id)
        score = get_eval(st, player_id)  # score from our perspective (player_id)
        candidates.append((score, seq, st))

    candidates.sort(key=lambda x: x[0], reverse=True)
    beam_candidates = candidates[:beam_width]

    if verbose:
        print(f"Root generated {len(root_moves)} moves, beam width = {len(beam_candidates)}")

    # 4) Expectation over opponent dice permutations
    outcomes = unordered_dice_outcomes_with_weights()
    total_weight = sum(w for _, w in outcomes)

    best_seq = None
    best_value = -math.inf

    for base_score, seq, st_after_root in beam_candidates:
        # immediate win
        if st_after_root.bear_off.get(player_id, 0) == 15:
            return seq

        # expected value over opponent dice
        weighted_sum = 0.0
        for dice_opp, w_opp in outcomes:
            # generate opponent moves for that dice
            opp_moves = st_after_root.generate_all_sequences_for_dice(opponent_id, dice_opp)

            if not opp_moves:
                # opponent can't move => evaluate static board
                v = get_eval(st_after_root, player_id)
                weighted_sum += v * w_opp
                continue

            # Order opponent moves by how good they are for opponent (i.e., worst for us)
            scored_opp = []
            for oseq in opp_moves:
                sst = st_after_root.clone()
                for m in oseq:
                    sst.apply_move(m, opponent_id)
                # Evaluate from *opponent* perspective, to know how good it is for them
                val_for_opponent = get_eval(sst, opponent_id)
                scored_opp.append((val_for_opponent, oseq, sst))

            # sort descending for opponent (best moves for opponent first)
            scored_opp.sort(key=lambda x: x[0], reverse=True)

            # Opponent will pick their best (which is worst for us). We only need top-N candidates.
            worst_value_for_us = math.inf
            take = min(opp_move_limit, len(scored_opp))
            for val_op, oseq, sst in scored_opp[:take]:
                # convert opponent-perspective value to our perspective:
                # since evaluate returns positive for opponent, a high val_op means bad for us.
                # we can compute our_value = -val_op (approx), but safer to re-evaluate from our perspective
                my_value = get_eval(sst, player_id)
                if my_value < worst_value_for_us:
                    worst_value_for_us = my_value

            weighted_sum += worst_value_for_us * w_opp

        expected_val = weighted_sum / total_weight
        if expected_val > best_value:
            best_value = expected_val
            best_seq = seq

    # fallback to best beam candidate if none selected
    if best_seq is None:
        best_seq = beam_candidates[0][1]
    return best_seq


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

