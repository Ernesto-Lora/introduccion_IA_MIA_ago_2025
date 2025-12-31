
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
        self.points = [0] * 24 
        self.bar = {PLAYER: 0, AI: 0}
        self.bear_off = {PLAYER: 0, AI: 0}
        self.current_player = PLAYER
        self.dice = ()       # <--- Atributo restaurado para la UI
        self.dice_left = []

    def clone(self):
        s = GameState()
        s.points = self.points[:]
        s.bar = self.bar.copy()
        s.bear_off = self.bear_off.copy()
        s.current_player = self.current_player
        s.dice = self.dice   # <--- Atributo restaurado
        s.dice_left = self.dice_left[:]
        return s

    def setup_standard(self):
        """Configuración inicial estándar de Backgammon."""
        self.points = [0] * 24
        # Jugador (Positivos: se mueven de 0 a 23)
        self.points[0]  = 2
        self.points[11] = 5
        self.points[16] = 3
        self.points[18] = 5
        # AI (Negativos: se mueven de 23 a 0)
        self.points[23] = -2
        self.points[12] = -5
        self.points[7]  = -3
        self.points[5]  = -5
        
        self.bar = {PLAYER: 0, AI: 0}
        self.bear_off = {PLAYER: 0, AI: 0}
        self.dice = ()
        self.dice_left = []

    def pip_count(self, player):
        """Calcula la distancia total restante para un jugador."""
        total = 0
        if player == PLAYER:
            # Distancia al punto 24 (fuera del tablero)
            total += self.bar[PLAYER] * 25
            for i, cnt in enumerate(self.points):
                if cnt > 0: total += cnt * (24 - i)
        else:
            # Distancia al punto -1 (fuera del tablero)
            total += self.bar[AI] * 25
            for i, cnt in enumerate(self.points):
                if cnt < 0: total += abs(cnt) * (i + 1)
        return total

    def can_bear_off(self, player):
        """Verifica si todas las fichas están en el último cuadrante."""
        if self.bar[player] > 0: return False
        if player == PLAYER:
            return sum(c for c in self.points[0:18] if c > 0) == 0
        else:
            return sum(abs(c) for c in self.points[6:24] if c < 0) == 0

    def is_valid_dest(self, player, dest):
        """Verifica si un punto está bloqueado (2+ fichas enemigas)."""
        if not (0 <= dest <= 23): return True # Bear-off se maneja aparte
        if player == PLAYER:
            return self.points[dest] >= -1 # Puede mover si hay 0, 1 o más fichas propias/enemigas
        else:
            return self.points[dest] <= 1

    def apply_move(self, move, player):
        if move is None: return False
        
        # 1. Origen
        if move.from_pt == "BAR":
            self.bar[player] -= 1
        else:
            if player == PLAYER: self.points[move.from_pt] -= 1
            else: self.points[move.from_pt] += 1

        # 2. Destino (Bear-off o Tablero)
        if (player == PLAYER and move.to_pt >= 24) or (player == AI and move.to_pt <= -1):
            self.bear_off[player] += 1
        else:
            target_val = self.points[move.to_pt]
            if player == PLAYER:
                if target_val == -1: # HITTING!
                    self.points[move.to_pt] = 1
                    self.bar[AI] += 1
                else:
                    self.points[move.to_pt] += 1
            else:
                if target_val == 1: # HITTING!
                    self.points[move.to_pt] = -1
                    self.bar[PLAYER] += 1
                else:
                    self.points[move.to_pt] -= 1

        if move.die_used in self.dice_left:
            self.dice_left.remove(move.die_used)
        return True

    def legal_single_moves_for_die(self, player, die):
        moves = []
        # Regla de Oro: Si hay fichas en la barra, DEBEN salir primero
        if self.bar[player] > 0:
            dest = (die - 1) if player == PLAYER else (24 - die)
            if self.is_valid_dest(player, dest):
                moves.append(Move("BAR", dest, die))
            return moves 

        for i in range(24):
            if (player == PLAYER and self.points[i] > 0) or (player == AI and self.points[i] < 0):
                dest = i + die if player == PLAYER else i - die
                if (player == PLAYER and dest >= 24) or (player == AI and dest <= -1):
                    if self.can_bear_off(player):
                        moves.append(Move(i, dest, die))
                elif 0 <= dest <= 23:
                    if self.is_valid_dest(player, dest):
                        moves.append(Move(i, dest, die))
        return moves

    def generate_all_sequences_for_dice(self, player, dice_tuple):
        """
        Generates all possible move sequences, trying both dice orders [A, B] and [B, A].
        """
        from itertools import permutations

        # 1. Handle Doubles (e.g., 2, 2 -> four 2s)
        if len(dice_tuple) == 2 and dice_tuple[0] == dice_tuple[1]:
            dice_lists = [[dice_tuple[0]] * 4]
        else:
            # 2. Handle standard dice: Try [2, 4] AND [4, 2]
            # This ensures if 2 is blocked but 4 is open, we find the move.
            dice_lists = list(set(permutations(dice_tuple)))

        all_final_sequences = []

        for d_list in dice_lists:
            sequences = [[]]
            states = [self.clone()]
            
            for die in d_list:
                new_sequences = []
                new_states = []
                for seq, st in zip(sequences, states):
                    moves = st.legal_single_moves_for_die(player, die)
                    
                    if not moves:
                        # If blocked, keep the current partial sequence
                        new_sequences.append(seq)
                        new_states.append(st)
                    else:
                        # If moves exist, branch out
                        for m in moves:
                            ns = st.clone()
                            ns.apply_move(m, player)
                            new_sequences.append(seq + [m])
                            new_states.append(ns)
                
                sequences = new_sequences
                states = new_states
                # REMOVED the "break" line here to allow subsequent dice to be tested
            
            all_final_sequences.extend(sequences)

        # 3. Filter duplicates and find the best moves
        # Backgammon Rule: You must use as many dice as possible.
        # So we filter for the longest sequences found.
        if not all_final_sequences:
            return []
            
        max_len = max(len(s) for s in all_final_sequences)
        
        # Only keep unique sequences of the maximum length found
        unique = []
        seen = set()
        for seq in all_final_sequences:
            # Only keep max length (Standard Backgammon Rule)
            if len(seq) == max_len: 
                key = tuple((m.from_pt, m.to_pt, m.die_used) for m in seq)
                if key not in seen:
                    seen.add(key)
                    unique.append(seq)
                    
        return unique