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

from gameState import GameState
from csp_arc_consistency import expectiminimax_one_ply_with_cutoff

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

        # ---- DIBUJAR LA BARRA (CENTRO) ----
        mid_x = left_x + 6 * POINT_W
        # Dibujar fichas del Jugador en la barra (arriba)
        if self.state.bar[PLAYER] > 0:
            self.draw_checkers_in_bar(PLAYER, mid_x, top_y + 50)
        # Dibujar fichas de la AI en la barra (abajo)
        if self.state.bar[AI] > 0:
            self.draw_checkers_in_bar(AI, mid_x, bot_y + POINT_H - 50)

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

    def draw_checkers_in_bar(self, player, x, start_y):
        cnt = self.state.bar[player]
        color = IVORY if player == PLAYER else BLACK
        border = BLACK if player == PLAYER else (245, 245, 245)
        spacing = 15
        for i in range(cnt):
            # Las fichas del jugador bajan, las de la AI suben
            y = start_y + (i * spacing) if player == PLAYER else start_y - (i * spacing)
            pygame.draw.circle(self.screen, color, (x, y), 12)
            pygame.draw.circle(self.screen, border, (x, y), 12, 2)


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
        mid_x = left_x + 6 * POINT_W  # Centro horizontal del tablero

        # 1. Manejo de la BARRA
        if pt_idx == "BAR":
            # Retorna el centro del tablero, entre la parte superior e inferior
            return mid_x, top_y + POINT_H // 2 + 20

        # 2. Manejo de Puntos normales (Aseguramos que sea entero para evitar TypeErrors)
        if isinstance(pt_idx, int):
            if pt_idx <= 11:
                i = 11 - pt_idx
                x = left_x + i * POINT_W + POINT_W // 2
                y = top_y + 40
                return x, y
            elif pt_idx <= 23:
                i = pt_idx - 12
                x = left_x + i * POINT_W + POINT_W // 2
                y = top_y + POINT_H + 40 + POINT_H - 40
                return x, y
            
        # 3. Manejo de Bear-off (Puntos 24 o -1)
        # Puedes retornar las coordenadas de tus cajas de bear-off aquí
        bear_x = left_x + 12 * POINT_W + 90
        if pt_idx >= 24: # Jugador
            return bear_x, top_y + 30
        if pt_idx <= -1: # AI
            return bear_x, top_y + POINT_H + 70
            
        return 0, 0 # Fallback

    def screen_to_point(self, mx, my):
        left_x = BOARD_X + GAP
        top_y = BOARD_Y + 20
        bot_y = top_y + POINT_H + 40
        mid_x = left_x + 6 * POINT_W  # Centro del tablero

        # --- NUEVO: Detección de la BARRA ---
        # Si el clic es en la franja central (ej. 40 píxeles de ancho)
        if mid_x - 20 <= mx <= mid_x + 20:
            if top_y <= my <= bot_y + POINT_H:
                return "BAR"

        # Puntos normales
        if left_x <= mx <= left_x + 12 * POINT_W:
            relx = mx - left_x
            idx = relx // POINT_W
            if top_y <= my <= top_y + POINT_H:
                return 11 - int(idx)
            if bot_y <= my <= bot_y + POINT_H:
                return 12 + int(idx)

        # Bear-off boxes
        bear_x = left_x + 12 * POINT_W + 20
        if bear_x <= mx <= bear_x + 140:
            if top_y <= my <= top_y + 60:
                return 24  # Usamos 24 como índice de salida para el Player
            if bot_y <= my <= bot_y + 60:
                return -1  # Usamos -1 para la AI (aunque la AI no hace click)
                
        return None
    def is_farthest_checker(self, pt_idx):
        """
        Para el PLAYER (puntos 18-23), verifica si no hay fichas 
        en puntos con menor índice que el actual dentro del home board.
        """
        if not (18 <= pt_idx <= 23):
            return False
            
        for i in range(18, pt_idx):
            if self.state.points[i] > 0:
                return False
        return True

    def get_legal_destinations_mapping_for_selected(self):
        mapping = {}
        if self.selected_point is None: return mapping
        
        sp = self.selected_point
        for d in self.state.dice_left:
            # Caso 1: Saliendo de la Barra
            if sp == "BAR":
                dest = d - 1
                if self.state.is_valid_dest(PLAYER, dest):
                    mapping.setdefault(dest, []).append(d)
                continue

            # Caso 2: Movimiento normal
            dest = sp + d
            if dest < 24:
                if self.state.is_valid_dest(PLAYER, dest):
                    mapping.setdefault(dest, []).append(d)
            # Caso 3: Bear-off (solo si can_bear_off es True)
            elif self.state.can_bear_off(PLAYER):
                # Regla: exacto o mayor si es la ficha más lejana
                if dest == 24 or (dest > 24 and self.is_farthest_checker(sp)):
                    mapping.setdefault(24, []).append(d)
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

        # --- FIX STARTS HERE ---
        possible_sequences = self.state.generate_all_sequences_for_dice(PLAYER, tuple(self.state.dice_left))
        
        # Check if ANY sequence has a length > 0. 
        # If the only result is [], it means no moves are possible.
        has_legal_moves = any(len(seq) > 0 for seq in possible_sequences)

        if not has_legal_moves:
            self.info = "No legal moves; turn skipped."
            print("[TURN] No legal moves for player; skipping turn.")
            pygame.display.flip() # Force render so user sees the text
            pygame.time.delay(1500) # Give user time to read
            self.end_player_turn()
            return


        # # If there are no legal sequences for the player with these dice, skip turn.
        # if not self.state.generate_all_sequences_for_dice(PLAYER, tuple(self.state.dice_left)):
        #     self.info = "No legal moves; turn skipped."
        #     print("[TURN] No legal moves for player; skipping turn.")
        #     pygame.time.delay(120)
        #     self.end_player_turn()
        #     return

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

        # 1. LÓGICA DE PRIORIDAD DE LA BARRA
        if self.state.bar[PLAYER] > 0:
            if pt == "BAR":
                self.selected_point = "BAR"
                self.info = "Barra seleccionada. ¡Debes entrar al tablero!"
                print("[SELECT] Selected BAR")
                return
            elif self.selected_point != "BAR":
                self.info = "¡Primero debes mover tus fichas de la BARRA!"
                return

        # 2. MANEJO DE BEAR-OFF (Clic en la caja de salida)
        # Usamos 24 como el índice de bear-off definido en screen_to_point
        if pt == 24: 
            if self.selected_point is not None:
                self.try_move_selected_to_bearoff()
            return

        # 3. SELECCIÓN INICIAL (Si no hay nada seleccionado)
        if self.selected_point is None:
            # Validamos que pt sea int antes de comparar
            if isinstance(pt, int) and 0 <= pt < 24:
                if self.state.points[pt] > 0:
                    self.selected_point = pt
                    self.info = f"Selected point {pt + 1}"
                    print(f"[SELECT] Selected {pt+1}")
                else:
                    self.info = "Select a point with your checkers."
            return

        # 4. INTENTO DE MOVIMIENTO (Si ya hay algo seleccionado)
        if pt == self.selected_point:
            self.selected_point = None
            self.info = "Selection cleared."
            return

        legal_map = self.get_legal_destinations_mapping_for_selected()
        
        if pt in legal_map:
            # Buscamos el dado que corresponde a este movimiento
            dice_options = legal_map.get(pt, [])
            die_to_use = dice_options[0] if dice_options else None

            if die_to_use is not None:
                m = Move(self.selected_point, pt, die_to_use)
                success = self.state.apply_move(m, PLAYER)
                if success:
                    print(f"[MOVE] Player {m.from_pt}->{m.to_pt} using die {m.die_used}")
                    self.selected_point = None
                    
                    if not self.state.dice_left:
                        self.end_player_turn()
                    else:
                        # --- FIX STARTS HERE ---
                        possibilities = self.state.generate_all_sequences_for_dice(PLAYER, tuple(self.state.dice_left))
                        has_legal_moves = any(len(seq) > 0 for seq in possibilities)
                        
                        if not has_legal_moves:
                            self.info = "No legal moves left; turn skipped."
                            pygame.display.flip()
                            pygame.time.delay(1000)
                            self.end_player_turn()
                        else:
                            self.info = f"Moved. Dice left: {self.state.dice_left}"
                        # --- FIX ENDS HERE ---

                return

        # 5. CAMBIO DE SELECCIÓN (Si el destino no es válido pero es otra ficha propia)
        if isinstance(pt, int) and 0 <= pt < 24 and self.state.points[pt] > 0:
            if self.state.bar[PLAYER] == 0: # Solo si no estamos obligados a mover de la barra
                self.selected_point = pt
                self.info = f"Changed selection to point {pt + 1}"
            return

        self.info = "Invalid destination."

    def try_move_selected_to_bearoff(self):
        if self.selected_point is None:
            return
            
        # 1. Regla fundamental: No se puede hacer bear-off si hay fichas en la barra
        if self.selected_point == "BAR" or self.state.bar[PLAYER] > 0:
            self.info = "¡Debes meter todas las fichas al tablero primero!"
            print("[INFO] Bear-off bloqueado: fichas en la barra.")
            return

        # 2. Calculamos la distancia al "punto 24" (fuera del tablero)
        # Si la ficha está en el índice 23, está a 1 paso de salir.
        dist = 24 - self.selected_point
        
        # 3. Consultamos el mapa de movimientos legales
        # Usamos 24 como la clave para el destino de bear-off del Jugador
        legal_map = self.get_legal_destinations_mapping_for_selected()
        
        if 24 not in legal_map:
            self.info = "No puedes sacar esta ficha aún."
            return

        # 4. Seleccionamos el dado adecuado
        # Obtenemos los dados que permiten este bear-off
        dice_options = legal_map.get(24, [])
        if not dice_options:
            return
            
        # Ordenamos para usar el dado más pequeño posible que cumpla el movimiento
        # (Opcional, depende de tu estrategia, pero suele ser lo estándar)
        dice_options.sort()
        d = dice_options[0]

        # 5. Aplicamos el movimiento
        m = Move(self.selected_point, 24, d)
        success = self.state.apply_move(m, PLAYER)
        
        if success:
            print(f"[MOVE] Bearing off from {m.from_pt} using die {d}")
            self.selected_point = None
            
            # Verificación de fin de turno
            if not self.state.dice_left:
                self.end_player_turn()
            elif not self.state.generate_all_sequences_for_dice(PLAYER, tuple(self.state.dice_left)):
                self.info = "No hay más movimientos legales; turno terminado."
                self.end_player_turn()
            else:
                self.info = f"Ficha fuera. Dados restantes: {self.state.dice_left}"
        else:
            self.info = "Movimiento de salida inválido."


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
        pygame.time.delay(200) 

        # Búsqueda detallada de la mejor secuencia usando Expectiminimax
        seq = expectiminimax_one_ply_with_cutoff(self.state, top_k_ai=14, top_k_opp=10, verbose=True)
        
        if seq:
            for m in seq:
                pygame.time.delay(150) 
                applied = self.state.apply_move(m, AI)
                if not applied:
                    print("[WARN] AI tried invalid move (skipping).")
                    continue
                
                # --- Lógica de formateo para el log ---
                # Si es "BAR", lo dejamos como texto. Si es int, sumamos 1 para visualización (1-24).
                from_label = "BAR" if m.from_pt == "BAR" else m.from_pt + 1
                
                # Para la AI, cualquier destino <= -1 es Bear-off (BO).
                to_label = "BO" if m.to_pt <= -1 else m.to_pt + 1
                
                print(f"[MOVE] AI {from_label} -> {to_label} ({m.die_used}). dice_left now={self.state.dice_left}")
        else:
            print("[INFO] AI has no legal moves. Skipping turn.")
            self.info = "AI has no legal moves."
            pygame.display.flip() # Update screen to show the message
            pygame.time.delay(1000) # Give the user time to read it

        # Finalizar turno y devolver control al jugador
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
    