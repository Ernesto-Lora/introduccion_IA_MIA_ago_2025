
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
        """Genera todas las combinaciones de movimientos posibles para un turno."""
        # Expandir dados si son dobles
        dice_list = list(dice_tuple)
        if len(dice_list) == 2 and dice_list[0] == dice_list[1]:
            dice_list = [dice_list[0]] * 4

        sequences = [[]]
        states = [self.clone()]

        for die in dice_list:
            new_sequences = []
            new_states = []
            for seq, st in zip(sequences, states):
                moves = st.legal_single_moves_for_die(player, die)
                if not moves:
                    new_sequences.append(seq)
                    new_states.append(st)
                else:
                    for m in moves:
                        ns = st.clone()
                        ns.apply_move(m, player)
                        new_sequences.append(seq + [m])
                        new_states.append(ns)
            sequences = new_sequences
            states = new_states
            if not any(len(s) > 0 for s in sequences): break

        # Eliminar duplicados
        unique = []
        seen = set()
        for seq in sequences:
            key = tuple((m.from_pt, m.to_pt, m.die_used) for m in seq)
            if key not in seen:
                seen.add(key)
                unique.append(seq)
        return unique