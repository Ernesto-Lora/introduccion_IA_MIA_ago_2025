import sys
import json
import argparse
from pathlib import Path
import pygame

# -----------------------------
# JSON loader
# -----------------------------
def load_all_solutions(json_path):
    """
    Load ALL positions from a JSON produced by the Prolog script.
    Returns: (n, list_of_solutions)
    
    Where list_of_solutions is a list of lists:
    [
      [(row, col), (row, col), ...],  # Solution 1
      [(row, col), (row, col), ...],  # Solution 2
      ...
    ]
    """
    try:
        text = Path(json_path).read_text(encoding="utf-8")
        data = json.loads(text)
    except Exception as e:
        raise ValueError(f"Failed to read JSON: {e}")

    n = int(data.get("n", 8))
    formatted_solutions = []

    # Case 1: Multiple solutions ("solutions" key)
    if "solutions" in data:
        raw_sols = data["solutions"]
        for sol in raw_sols:
            # Check format of individual solution
            if isinstance(sol, list) and len(sol) > 0 and isinstance(sol[0], dict):
                # Format: [{"col":1, "row":1}, ...]
                # Note: We ensure we read 'row' and 'col' correctly regardless of order
                formatted_solutions.append([(item["row"], item["col"]) for item in sol])
            elif isinstance(sol, list) and len(sol) > 0 and isinstance(sol[0], int):
                # Format: [4, 2, 7, ...] (List of column indices per row)
                formatted_solutions.append([(r + 1, c) for r, c in enumerate(sol)])
            else:
                # Handle empty lists or unknown formats if necessary
                pass

    # Case 2: Single solution ("solution" key) - Old format
    elif "solution" in data:
        sol = data["solution"]
        # Wrap it in a list to treat it uniformly as a list of solutions
        positions = [(item["row"], item["col"]) for item in sol]
        formatted_solutions.append(positions)
    
    else:
        raise ValueError("Invalid JSON schema. Expect 'solution' or 'solutions' keys.")

    if not formatted_solutions:
        raise ValueError("No valid solutions found in the file.")

    return n, formatted_solutions


# -----------------------------
# Pygame drawing
# -----------------------------
def draw_board(n, all_solutions, crown_path="crown.png", square_size=80):
    """
    Interactive viewer for N-Queens.
    """
    pygame.init()
    pygame.font.init()

    # Font for UI overlay
    font = pygame.font.SysFont("Arial", 24, bold=True)

    # Compute board size
    board_size = n * square_size
    screen = pygame.display.set_mode((board_size, board_size))
    
    # Load crown image
    crown_img = None
    try:
        img = pygame.image.load(crown_path).convert_alpha()
        margin = max(6, square_size // 10)
        target_w = target_h = square_size - margin
        crown_img = pygame.transform.smoothscale(img, (target_w, target_h))
    except Exception as e:
        print(f"[warn] Could not load crown image '{crown_path}'. Using fallback.")

    # Colors
    white = (240, 240, 240)
    gray  = (100, 100, 100)
    red   = (200, 40, 40)
    blue  = (20, 20, 200)

    clock = pygame.time.Clock()
    
    current_idx = 0
    total_sols = len(all_solutions)
    running = True

    print("\n[Controls]")
    print(" -> Right Arrow : Next Solution")
    print(" <- Left Arrow  : Previous Solution")
    print("    ESC         : Quit\n")

    while running:
        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_RIGHT:
                    current_idx = (current_idx + 1) % total_sols
                elif event.key == pygame.K_LEFT:
                    current_idx = (current_idx - 1) % total_sols

        # Update Window Title
        pygame.display.set_caption(f"{n}-Queens | Solution {current_idx + 1} of {total_sols}")

        # Current positions to draw
        positions = all_solutions[current_idx]

        # Draw chessboard
        for row in range(n):
            for col in range(n):
                color = white if (row + col) % 2 == 0 else gray
                pygame.draw.rect(
                    screen, color,
                    (col * square_size, row * square_size, square_size, square_size)
                )

        # Draw crowns
        for (row, col) in positions:
            # 1-based index to 0-based pixel coordinates
            pixel_x = (col - 1) * square_size
            pixel_y = (row - 1) * square_size

            if crown_img:
                x = pixel_x + (square_size - crown_img.get_width()) // 2
                y = pixel_y + (square_size - crown_img.get_height()) // 2
                screen.blit(crown_img, (x, y))
            else:
                center = (pixel_x + square_size // 2, pixel_y + square_size // 2)
                radius = max(8, (square_size // 2) - 7)
                pygame.draw.circle(screen, red, center, radius)

        # Draw UI Overlay (Solution Counter)
        text_surf = font.render(f"Sol: {current_idx + 1}/{total_sols}", True, blue)
        screen.blit(text_surf, (10, 10))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


# -----------------------------
# CLI
# -----------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="Visualize all N-Queens solutions interactively.")
    parser.add_argument("--json", type=str, required=True, help="Path to JSON file exported by Prolog.")
    parser.add_argument("--square", type=int, default=80, help="Square size in pixels.")
    parser.add_argument("--crown", type=str, default="crown.png", help="Path to crown image (PNG).")
    return parser.parse_args()


def main():
    args = parse_args()
    json_path = args.json
    crown_path = args.crown
    square_size = max(24, args.square)

    try:
        n, all_sols = load_all_solutions(json_path)
    except Exception as e:
        print(f"[error] Could not load positions: {e}")
        sys.exit(1)

    print(f"[info] Loaded {len(all_sols)} solutions for n={n} from {json_path}.")
    draw_board(n, all_sols, crown_path=crown_path, square_size=square_size)


if __name__ == "__main__":
    main()