"""
Backgammon (pygame) - didactic expectiminimax AI (one decision ply).

Minimal modifications (option A): shorten blocking delays so the UI feels
more responsive while preserving human-readable AI pacing and console
search output for educational purposes.

- Reduced AI and turn delays (was 800/600/400 etc — now much shorter).
- Kept same game logic, selection-first-try-move behavior, and verbose AI search.
- Kept stacked piece drawing (no compact/list modes).

Run from a terminal to see the AI search prints.

-----------------------------------------------------------------------------------------

The game enters a deadlock when the player has remaining dice values but no legal moves 
(e.g., all possible destinations are blocked by the opponent). In this state, the UI 
continues to wait for user interaction, and the turn never ends, forcing the player to 
close the application manually. This occurs because the logic only checks for legal moves 
after an attempted move, not globally before interaction.

------------------------------------------------------------------------------------------

"""
import pygame
import sys
import random
from collections import namedtuple

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

# ---- Game state and move generation ----
class GameState:
    def __init__(self):
        self.points = [0] * NUM_POINTS
        self.bear_off = {PLAYER: 0, AI: 0}
        self.current_player = PLAYER
        self.dice = ()
        self.dice_left = []

    def clone(self):
        s = GameState()
        s.points = self.points[:]
        s.bear_off = self.bear_off.copy()
        s.current_player = self.current_player
        s.dice = self.dice
        s.dice_left = self.dice_left[:]
        return s

    def setup_standard(self):
        self.points = [0] * NUM_POINTS
        # a simplified starting setup (didactic)
        self.points[0] = 2
        self.points[11] = 5
        self.points[16] = 3
        self.points[18] = 5
        self.points[5] = -5
        self.points[7] = -3
        self.points[12] = -5
        self.points[23] = -2
        self.bear_off = {PLAYER: 0, AI: 0}
        self.current_player = PLAYER
        self.dice = ()
        self.dice_left = []

    def pip_count(self, player):
        total = 0
        if player == PLAYER:
            for i, cnt in enumerate(self.points):
                if cnt > 0:
                    total += cnt * (NUM_POINTS - 1 - i)
        else:
            for i, cnt in enumerate(self.points):
                if cnt < 0:
                    total += (-cnt) * i
        return total

    def apply_move(self, move, player):
        """Apply a single move. Return True on success, False on invalid move."""
        if move is None:
            return False
        if player == PLAYER:
            if move.from_pt is None or move.to_pt is None:
                return False
            if move.from_pt < 0 or move.from_pt >= NUM_POINTS:
                return False
            if self.points[move.from_pt] <= 0:
                return False
            if move.to_pt != NUM_POINTS:
                if move.to_pt < 0 or move.to_pt >= NUM_POINTS:
                    return False
                if self.points[move.to_pt] < 0:
                    return False
            self.points[move.from_pt] -= 1
            if move.to_pt == NUM_POINTS:
                self.bear_off[PLAYER] += 1
            else:
                self.points[move.to_pt] += 1
        else:  # AI
            if move.from_pt is None or move.to_pt is None:
                return False
            if move.from_pt < 0 or move.from_pt >= NUM_POINTS:
                return False
            if self.points[move.from_pt] >= 0:
                return False
            if move.to_pt != -1:
                if move.to_pt < 0 or move.to_pt >= NUM_POINTS:
                    return False
                if self.points[move.to_pt] > 0:
                    return False
            self.points[move.from_pt] += 1
            if move.to_pt == -1:
                self.bear_off[AI] += 1
            else:
                self.points[move.to_pt] -= 1

        # consume die only after successful application
        if move.die_used in self.dice_left:
            self.dice_left.remove(move.die_used)
        return True

    def legal_single_moves_for_die(self, player, die):
        """Generate legal single-step moves for the given die (no-hitting simplified)."""
        moves = []
        if player == PLAYER:
            for i in range(NUM_POINTS):
                if self.points[i] > 0:
                    dest = i + die
                    if dest <= NUM_POINTS - 1:
                        if self.points[dest] < 0:
                            continue
                        moves.append(Move(i, dest, die))
                    else:
                        moves.append(Move(i, NUM_POINTS, die))
        else:
            for i in range(NUM_POINTS - 1, -1, -1):
                if self.points[i] < 0:
                    dest = i - die
                    if dest >= 0:
                        if self.points[dest] > 0:
                            continue
                        moves.append(Move(i, dest, die))
                    else:
                        moves.append(Move(i, -1, die))
        return moves

    def generate_all_sequences_for_dice(self, player, dice):
        """Generate all legal sequences for the given dice tuple (expand doubles)."""
        dice_list = []
        if len(dice) == 2 and dice[0] == dice[1]:
            dice_list = [dice[0]] * 4
        else:
            dice_list = list(dice)

        sequences = [[]]
        states = [self.clone()]

        for die in dice_list:
            new_sequences = []
            new_states = []
            for seq, st in zip(sequences, states):
                st_local = st.clone()
                st_local.dice_left = st_local.dice_left[:]
                moves = st_local.legal_single_moves_for_die(player, die)
                if not moves:
                    new_sequences.append(seq[:])
                    new_states.append(st.clone())
                else:
                    for m in moves:
                        ns = st.clone()
                        ns.dice_left = st.dice_left[:]
                        ns.apply_move(m, player)
                        new_sequences.append(seq + [m])
                        new_states.append(ns)
            sequences = new_sequences
            states = new_states
            if not sequences:
                break

        # deduplicate
        unique = []
        seen = set()
        for seq in sequences:
            key = tuple((m.from_pt, m.to_pt, m.die_used) for m in seq)
            if key not in seen:
                seen.add(key)
                unique.append(seq)
        return unique

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
def expectiminimax_one_ply_with_cutoff(state: GameState, top_k_ai=14, top_k_opp=10, verbose=False):
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
        if verbose:
            print(f"\nCandidate {idx+1}: immediate eval {base_val:.3f} (seq len {len(seq)})")
        if st_after_ai.bear_off[AI] >= 15:
            if verbose:
                print(" Immediate AI win detected for this candidate; selecting it.")
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

            if verbose:
                print(f"  outcome {outcome} w={weight} -> opp_best={opp_best_val:.3f}, partial_sum={partial_sum:.3f}, optimistic_expected={optimistic_expected:.3f}, best_so_far={best_expected:.3f}")

            if optimistic_expected >= best_expected:
                pruned = True
                if verbose:
                    print("  -> Candidate pruned by optimistic bound (cutoff).")
                break

        if not pruned:
            expected_val = partial_sum / total_weight
            if verbose:
                print(f" Candidate final expected value = {expected_val:.3f}")
            if expected_val < best_expected:
                best_expected = expected_val
                best_seq = seq
                if verbose:
                    print(f"  -> New best candidate (expected {best_expected:.3f})")

    if best_seq is None:
        if verbose:
            print("All candidates pruned; falling back to first immediate-best candidate.")
        return candidates[0][1]
    return best_seq

# ---- Pygame UI ----
class BackgammonUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Backgammon - Expectiminimax")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16)
        self.bigfont = pygame.font.SysFont("Arial", 20)
        self.state = GameState()
        self.state.setup_standard()
        self.selected_point = None
        self.info = "Your turn. Press R to roll dice. (AI search prints to console)"
        self.need_roll = True
        self.running = True

    def render_text_with_stroke(self, text, font, color, stroke_color):
        base = font.render(text, True, color)
        w, h = base.get_size()
        surf = pygame.Surface((w + 2, h + 2), pygame.SRCALPHA)
        offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for ox, oy in offsets:
            s = font.render(text, True, stroke_color)
            surf.blit(s, (ox + 1, oy + 1))
        surf.blit(base, (1, 1))
        return surf

    def draw_board(self):
        self.screen.fill(BG)
        pygame.draw.rect(self.screen, WOOD, (BOARD_X, BOARD_Y, POINT_W * 12 * 2 + GAP * 2, POINT_H * 2 + 80), border_radius=6)
        left_x = BOARD_X + GAP
        top_y = BOARD_Y + 20

        # top points
        for i in range(12):
            pt_idx = 11 - i
            x = left_x + i * POINT_W
            color = TRI_A if i % 2 == 0 else TRI_B
            pygame.draw.polygon(self.screen, color, [(x, top_y), (x + POINT_W, top_y), (x + POINT_W // 2, top_y + POINT_H)])
            num_surf = self.render_text_with_stroke(str(pt_idx + 1), self.bigfont, TEXT_COLOR, STRIKE_COLOR)
            self.screen.blit(num_surf, (x + POINT_W // 2 - num_surf.get_width() / 2, top_y + 4))
            self.draw_checkers_at_point(pt_idx, x + POINT_W // 2, top_y + 30, pointing_down=True)

        bot_y = top_y + POINT_H + 40
        # bottom points
        for i in range(12):
            pt_idx = 12 + i
            x = left_x + i * POINT_W
            color = TRI_A if i % 2 == 0 else TRI_B
            pygame.draw.polygon(self.screen, color, [(x, bot_y + POINT_H), (x + POINT_W, bot_y + POINT_H), (x + POINT_W // 2, bot_y)])
            num_surf = self.render_text_with_stroke(str(pt_idx + 1), self.bigfont, TEXT_COLOR, STRIKE_COLOR)
            self.screen.blit(num_surf, (x + POINT_W // 2 - num_surf.get_width() / 2, bot_y + POINT_H - 20))
            self.draw_checkers_at_point(pt_idx, x + POINT_W // 2, bot_y + POINT_H - 30, pointing_down=False)

        # center line
        mid_x = left_x + 6 * POINT_W
        pygame.draw.line(self.screen, BLACK, (mid_x, top_y - 10), (mid_x, bot_y + POINT_H + 10), 3)

        # bear-off boxes
        bear_x = left_x + 12 * POINT_W + 20
        pygame.draw.rect(self.screen, (200, 200, 200), (bear_x, top_y, 140, 60))
        pygame.draw.rect(self.screen, (200, 200, 200), (bear_x, bot_y, 140, 60))
        # draw dice and info
        dice_text = f"Dice: {self.state.dice if self.state.dice else '-'}   Dice left: {self.state.dice_left}"
        self.screen.blit(self.bigfont.render(dice_text, True, TEXT_COLOR), (BOARD_X, HEIGHT - 70))
        self.screen.blit(self.font.render(self.info, True, TEXT_COLOR), (BOARD_X + 8, HEIGHT - 40))
        # bear-off counts drawn near boxes
        p_text = self.font.render(f"You BO: {self.state.bear_off[PLAYER]}", True, TEXT_COLOR)
        a_text = self.font.render(f"AI BO: {self.state.bear_off[AI]}", True, TEXT_COLOR)
        self.screen.blit(p_text, (bear_x + 6, top_y + 8))
        self.screen.blit(a_text, (bear_x + 6, bot_y + 8))

        # selection and legal markers
        if self.selected_point is not None and self.state.current_player == PLAYER:
            x, y = self.point_to_screen(self.selected_point)
            pygame.draw.circle(self.screen, HIGHLIGHT, (x, y), 18, 3)
            legal_map = self.get_legal_destinations_mapping_for_selected()
            for dest in legal_map.keys():
                if dest == NUM_POINTS:
                    bx = bear_x + 70
                    by = top_y + 30
                    pygame.draw.circle(self.screen, LEGAL_MARKER, (int(bx), int(by)), 10)
                    pygame.draw.circle(self.screen, BLACK, (int(bx), int(by)), 10, 2)
                else:
                    dx, dy = self.point_to_screen(dest)
                    pygame.draw.circle(self.screen, LEGAL_MARKER, (dx, dy), 10)
                    pygame.draw.circle(self.screen, BLACK, (dx, dy), 10, 2)

    def draw_checkers_at_point(self, pt_idx, center_x, start_y, pointing_down=True):
        cnt = self.state.points[pt_idx]
        abs_cnt = abs(cnt)
        if abs_cnt == 0:
            return
        # stacked drawing: more readable for educational purposes
        max_stack = 8
        spacing = 8
        color = IVORY if cnt > 0 else BLACK
        border = BLACK if cnt > 0 else (245, 245, 245)
        for i in range(min(abs_cnt, max_stack)):
            if pointing_down:
                y = start_y + i * (12 + spacing)
            else:
                y = start_y - i * (12 + spacing)
            pygame.draw.circle(self.screen, color, (center_x, y), 12)
            pygame.draw.circle(self.screen, border, (center_x, y), 12, 2)
        if abs_cnt > max_stack:
            more_txt = self.font.render(f"+{abs_cnt - max_stack}", True, TEXT_COLOR)
            if pointing_down:
                self.screen.blit(more_txt, (center_x - more_txt.get_width() / 2, start_y + max_stack * (12 + spacing)))
            else:
                self.screen.blit(more_txt, (center_x - more_txt.get_width() / 2, start_y - max_stack * (12 + spacing) - more_txt.get_height()))

    def point_to_screen(self, pt_idx):
        left_x = BOARD_X + GAP
        top_y = BOARD_Y + 20
        if pt_idx <= 11:
            i = 11 - pt_idx
            x = left_x + i * POINT_W + POINT_W // 2
            y = top_y + 40
        else:
            i = pt_idx - 12
            x = left_x + i * POINT_W + POINT_W // 2
            y = top_y + POINT_H + 40 + POINT_H - 40
        return x, y

    def screen_to_point(self, mx, my):
        left_x = BOARD_X + GAP
        top_y = BOARD_Y + 20
        bot_y = top_y + POINT_H + 40
        if left_x <= mx <= left_x + 12 * POINT_W:
            relx = mx - left_x
            idx = relx // POINT_W
            if top_y <= my <= top_y + POINT_H:
                return 11 - int(idx)
            if bot_y <= my <= bot_y + POINT_H:
                return 12 + int(idx)
        # bear-off boxes clicks
        bear_x = left_x + 12 * POINT_W + 20
        if bear_x <= mx <= bear_x + 140:
            if top_y <= my <= top_y + 60:
                return NUM_POINTS + 1
            if bot_y <= my <= bot_y + 60:
                return NUM_POINTS + 2
        return None

    def get_legal_destinations_mapping_for_selected(self):
        mapping = {}
        if self.selected_point is None:
            return mapping
        if not self.state.dice_left:
            return mapping
        sp = self.selected_point
        for d in self.state.dice_left:
            dest = sp + d
            if dest <= NUM_POINTS - 1:
                if self.state.points[dest] < 0:
                    continue
                mapping.setdefault(dest, []).append(d)
            else:
                dist = NUM_POINTS - sp
                if d >= dist:
                    mapping.setdefault(NUM_POINTS, []).append(d)
        return mapping

    # ---- interactions ----
    def run(self):
        while self.running:
            self.clock.tick(FPS)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    self.on_click(ev.pos)
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_r:
                        if self.state.current_player == PLAYER and self.need_roll:
                            self.roll_for_player()
                    elif ev.key == pygame.K_SPACE:
                        if self.state.current_player == AI:
                            self.do_ai_turn()
            self.draw_board()
            pygame.display.flip()
            if self.state.bear_off[PLAYER] >= 15:
                print("You won!")
                self.running = False
            elif self.state.bear_off[AI] >= 15:
                print("AI won!")
                self.running = False
        pygame.time.wait(200)
        pygame.quit()
        sys.exit()

    def roll_for_player(self):
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        if d1 == d2:
            self.state.dice = (d1, d1)
            self.state.dice_left = [d1] * 4
        else:
            self.state.dice = (d1, d2)
            self.state.dice_left = [d1, d2]
        self.need_roll = False
        self.info = f"You rolled {self.state.dice}"
        print(f"[ROLL] You rolled {self.state.dice}. dice_left={self.state.dice_left}")

        # If there are no legal sequences for the player with these dice, skip turn.
        if not self.state.generate_all_sequences_for_dice(PLAYER, tuple(self.state.dice_left)):
            self.info = "No legal moves; turn skipped."
            print("[TURN] No legal moves for player; skipping turn.")
            pygame.time.delay(120)
            self.end_player_turn()
            return

    def on_click(self, pos):
        mx, my = pos
        pt = self.screen_to_point(mx, my)
        if self.state.current_player != PLAYER:
            return
        if self.need_roll:
            self.info = "Press R to roll dice first."
            return
        if pt is None:
            return
        if pt == NUM_POINTS + 1:
            # top bear-off box clicked
            if self.selected_point is not None:
                self.try_move_selected_to_bearoff()
            return

        # selection handling
        if self.selected_point is None:
            if 0 <= pt < NUM_POINTS and self.state.points[pt] > 0:
                self.selected_point = pt
                self.info = f"Selected point {pt + 1}"
                print(f"[SELECT] Selected {pt+1} (count {self.state.points[pt]})")
            else:
                self.info = "Select a point with your checkers."
            return

        # if a point already selected, try the click as a destination first
        if 0 <= pt < NUM_POINTS:
            if pt == self.selected_point:
                self.selected_point = None
                self.info = "Selection cleared."
                print("[SELECT] Selection cleared")
                return

            legal_map = self.get_legal_destinations_mapping_for_selected()
            if pt in legal_map:
                distance = pt - self.selected_point
                if distance <= 0:
                    if self.state.points[pt] > 0:
                        self.selected_point = pt
                        self.info = f"Changed selection to point {pt + 1}"
                        print(f"[SELECT] Changed selection to {pt+1}")
                    else:
                        self.info = "You must move forward (to higher points)."
                    return

                dice_options = legal_map.get(pt, [])
                die_to_use = None
                for d in self.state.dice_left:
                    if d in dice_options:
                        die_to_use = d
                        break
                if die_to_use is None:
                    self.info = f"No matching die for distance {distance}."
                    return

                m = Move(self.selected_point, pt, die_to_use)
                success = self.state.apply_move(m, PLAYER)
                if success:
                    print(f"[MOVE] Player {m.from_pt+1}->{m.to_pt+1} using die {m.die_used}. dice_left now={self.state.dice_left}")
                    self.selected_point = None
                    # If no dice left, end turn immediately
                    if not self.state.dice_left:
                        self.info = f"Moved by {m.die_used}. Dice left: {self.state.dice_left}"
                        self.end_player_turn()
                        return
                    # If there are dice left but no legal sequences with remaining dice, skip turn.
                    if not self.state.generate_all_sequences_for_dice(PLAYER, tuple(self.state.dice_left)):
                        self.info = f"No legal moves with remaining dice {self.state.dice_left}; turn skipped."
                        print("[TURN] No legal moves with remaining dice; skipping turn.")
                        pygame.time.delay(120)
                        self.end_player_turn()
                        return
                    # otherwise continue player's turn
                    self.info = f"Moved by {m.die_used}. Dice left: {self.state.dice_left}"
                else:
                    print(f"[WARN] Invalid move attempted: {m}")
                    self.info = "Invalid move."
                return

            # not a legal destination; if user clicked another own point -> change selection
            if self.state.points[pt] > 0:
                self.selected_point = pt
                self.info = f"Changed selection to point {pt + 1}"
                print(f"[SELECT] Changed selection to {pt+1}")
                return

            self.info = "Invalid destination."
            return

    def try_move_selected_to_bearoff(self):
        if self.selected_point is None:
            return
        dist = NUM_POINTS - self.selected_point
        legal_map = self.get_legal_destinations_mapping_for_selected()
        if NUM_POINTS not in legal_map:
            self.info = "No suitable die to bear off from selected point."
            print(f"[INFO] No bear-off allowed from {self.selected_point+1}. dice_left={self.state.dice_left}")
            return
        possible = [d for d in self.state.dice_left if d >= dist]
        if not possible:
            self.info = "No suitable die to bear off from selected point."
            return
        possible.sort()
        d = possible[0]
        m = Move(self.selected_point, NUM_POINTS, d)
        success = self.state.apply_move(m, PLAYER)
        if success:
            print(f"[MOVE] Bearing off from {m.from_pt+1} using die {d}. dice_left now={self.state.dice_left}")
            self.selected_point = None
            # If no dice left, end turn immediately
            if not self.state.dice_left:
                self.info = f"Bearing off with die {d}."
                self.end_player_turn()
                return
            # If there are dice left but no legal sequences with remaining dice, skip turn.
            if not self.state.generate_all_sequences_for_dice(PLAYER, tuple(self.state.dice_left)):
                self.info = f"No legal moves with remaining dice {self.state.dice_left}; turn skipped."
                print("[TURN] No legal moves with remaining dice; skipping turn.")
                pygame.time.delay(120)
                self.end_player_turn()
                return
            self.info = f"Bearing off with die {d}."
        else:
            print(f"[WARN] Invalid bear-off attempt: {m}")
            self.info = "Invalid bear-off."

    def end_player_turn(self):
        if self.state.bear_off[PLAYER] >= 15:
            print("You won!")
            self.running = False
            return
        self.need_roll = True
        self.state.dice = ()
        self.state.dice_left = []
        self.state.current_player = AI
        self.info = "AI thinking..."
        print("[TURN] AI thinking...")
        pygame.time.delay(120)  # shorter pause before AI starts
        self.do_ai_turn()

    def do_ai_turn(self):
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        if d1 == d2:
            self.state.dice = (d1, d1)
            self.state.dice_left = [d1] * 4
        else:
            self.state.dice = (d1, d2)
            self.state.dice_left = [d1, d2]
        self.info = f"AI rolled {self.state.dice}"
        print(f"[ROLL] AI rolled {self.state.dice}. dice_left={self.state.dice_left}")
        pygame.time.delay(200)  # shorter initial pause

        # show detailed AI search in console for educational purposes
        seq = expectiminimax_one_ply_with_cutoff(self.state, top_k_ai=14, top_k_opp=10, verbose=True)
        if seq:
            for m in seq:
                pygame.time.delay(150)  # shorter delay between AI moves
                applied = self.state.apply_move(m, AI)
                if not applied:
                    print("[WARN] AI tried invalid move (skipping).")
                    continue
                print(f"[MOVE] AI {m.from_pt+1}->{(m.to_pt+1) if m.to_pt!=-1 else 'BO'} ({m.die_used}). dice_left now={self.state.dice_left}")
        # finalize turn
        self.state.dice = ()
        self.state.dice_left = []
        self.state.current_player = PLAYER
        self.need_roll = True
        self.info = "Your turn. Press R to roll dice."
        print("[TURN] Your turn. Press R to roll dice.")

# ---- Run ----
def main():
    ui = BackgammonUI()
    ui.run()

if __name__ == "__main__":
    main()
    