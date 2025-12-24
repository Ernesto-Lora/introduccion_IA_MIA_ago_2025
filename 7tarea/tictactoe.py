import pygame
import sys

# --- Pygame Setup ---
pygame.init()
WIDTH, HEIGHT = 300, 300
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tic-Tac-Toe AI (Alpha-Beta)")
LINE_WIDTH = 5

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# --- Game Variables ---
# "X" is the player, "O" is the AI
board = [" " for _ in range(9)]
step_counter = 0 # To count minimax steps

# --- Drawing Functions ---
def draw_board():
    SCREEN.fill(WHITE)
    pygame.draw.line(SCREEN, BLACK, (100, 0), (100, 300), LINE_WIDTH)
    pygame.draw.line(SCREEN, BLACK, (200, 0), (200, 300), LINE_WIDTH)
    pygame.draw.line(SCREEN, BLACK, (0, 100), (300, 100), LINE_WIDTH)
    pygame.draw.line(SCREEN, BLACK, (0, 200), (300, 200), LINE_WIDTH)

def draw_marks():
    font = pygame.font.SysFont(None, 80)
    for i in range(9):
        x = (i % 3) * 100 + 30
        y = (i // 3) * 100 + 30
        if board[i] != " ":
            mark = font.render(board[i], True, BLACK)
            SCREEN.blit(mark, (x, y))

# --- Game Logic Functions ---
def check_winner(b, player):
    win_conditions = [
        [0,1,2], [3,4,5], [6,7,8], # Horizontal
        [0,3,6], [1,4,7], [2,5,8], # Vertical
        [0,4,8], [2,4,6],         # Diagonal
    ]
    for condition in win_conditions:
        if all(b[i] == player for i in condition):
            return True
    return False

def is_full(b):
    return all(cell != " " for cell in b)

# --- AI Implementation (Alpha-Beta Minimax) ---

def minimax(b, depth, is_maximizing, alpha, beta):
    """
    Minimax algorithm with Alpha-Beta Pruning.
    'O' is the maximizing player (AI).
    'X' is the minimizing player (Human).
    """
    global step_counter
    step_counter += 1

    # --- Base Cases (Terminal States) ---
    if check_winner(b, "X"): # Human wins
        return -10 + depth # Bad for AI, prefer to lose later
    if check_winner(b, "O"): # AI wins
        return 10 - depth  # Good for AI, prefer to win sooner
    if is_full(b): # Tie
        return 0

    # --- Maximizing Player's Turn (AI "O") ---
    if is_maximizing:
        best_score = -float("inf")
        for i in range(9):
            if b[i] == " ":
                b[i] = "O" # Make the move
                score = minimax(b, depth + 1, False, alpha, beta)
                b[i] = " " # Undo the move
                best_score = max(score, best_score)
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break # Beta cut-off (Minimizer already has a better option)
        return best_score
    
    # --- Minimizing Player's Turn (Human "X") ---
    else:
        best_score = float("inf")
        for i in range(9):
            if b[i] == " ":
                b[i] = "X" # Make the move
                score = minimax(b, depth + 1, True, alpha, beta)
                b[i] = " " # Undo the move
                best_score = min(score, best_score)
                beta = min(beta, best_score)
                if beta <= alpha:
                    break # Alpha cut-off (Maximizer already has a better option)
        return best_score

# Find best move for AI
def best_move():
    global step_counter
    step_counter = 0  # Reset counter before each move

    best_score = -float("inf")
    move = -1
    for i in range(9):
        if board[i] == " ":
            board[i] = "O" # Try the move
            # Call minimax for the "minimizing" player's response
            score = minimax(board, 0, False, -float("inf"), float("inf"))
            board[i] = " " # Undo the move
            
            if score > best_score:
                best_score = score
                move = i

    print(f"Alpha-Beta steps (recursive calls): {step_counter}")
    return move

# Main game loop
def main():
    global board # Make board modifiable
    running = True
    player_turn = True  # Player "X" starts
    game_over = False

    while running:
        draw_board()
        draw_marks()
        pygame.display.update()

        # --- AI's Turn ("O") ---
        if not player_turn and not game_over:
            ai_move = best_move()
            if ai_move != -1:
                board[ai_move] = "O"
                player_turn = True # Set back to player's turn
            
            if check_winner(board, "O"):
                print("AI Wins!")
                game_over = True
            elif is_full(board):
                print("It's a Tie!")
                game_over = True

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                sys.exit()

            # --- Player's Turn ("X") ---
            if player_turn and not game_over and event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                row = y // 100
                col = x // 100
                idx = row * 3 + col
                
                if board[idx] == " ":
                    board[idx] = "X"
                    player_turn = False # Set to AI's turn
                    
                    if check_winner(board, "X"):
                        print("Player Wins!")
                        game_over = True
                    elif is_full(board):
                        print("It's a Tie!")
                        game_over = True

            # --- Restart Game ---
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Reset all game variables
                    board = [" " for _ in range(9)]
                    player_turn = True
                    game_over = False
                    print("\n--- New Game ---")

# Start the game
if __name__ == "__main__":
    main()