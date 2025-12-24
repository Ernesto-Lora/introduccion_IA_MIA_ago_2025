
The file **queens8_all.json** contains all possible solutions to the classic *8-queens* chess problem.
You can generate it by running:

```
swipl n_queens_all.pl 8
```

## Implementation Notes

To compute all solutions, we use **solve_one_solution/2** to find each valid configuration and then gather them with:

```prolog
findall(Cols, solve_one_solution(Cols, N), AllCols)
```

To save the results into a JSON file, we use `maplist/3` to format each solution:

```prolog
maplist(solution_to_dicts, AllCols, AllSolutionsFormatted)
```


# N-Queens Visualizer

A Python script to interactively visualize multiple solutions for the N-Queens problem using Pygame.

## How to Run

1. **Install Pygame:**
```bash
   pip install pygame
````

2.  **Execute the script:**

    ```bash
    python draw_queens.py --json queens8_all.json
    ```

    *Optional arguments:* `--square 80` (size in pixels), `--crown crown.png` (custom image).

3.  **Controls:**

      - **Right Arrow:** Next solution
      - **Left Arrow:** Previous solution
      - **ESC:** Quit

## Changes 

  - **JSON Loading:** The script was updated to parse the `"solutions"` key, which contains a list of all possible board configurations (e.g., `[ [{col:1, row:1}...], [...] ]`), rather than a single solution.
  - **Memory:** Instead of selecting a specific index via command line arguments, the script now loads **all** solutions into memory at startup.
  - **Interactivity:** The Pygame loop now includes event handling for keyboard input, updating the displayed board index dynamically without restarting the application.

<!-- end list -->
