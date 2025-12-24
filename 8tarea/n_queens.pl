/*
   N_Queens in Prolog with JSON export
   ------------------------------------
   - Solves exactly ONE solution for a given N (passed as command-line argument).
   - Exports the solution to a JSON file named queen<N>.json.
   - Usage:
       swipl -q -s n_queens.pl -- 8
*/

:- use_module(library(clpfd)).        % Constraint Logic Programming over Finite Domains
:- use_module(library(http/json)).    % JSON read/write support
:- initialization(main, main).

% --- Main entry point ---------------------------------------------------------
% Reads N from command-line arguments, solves the N-Queens problem, and writes JSON.
main :-
    current_prolog_flag(argv, Argv),
    ( Argv = [NAtom|_] ->
        atom_number(NAtom, N),                     % Convert argument to integer
        solve_one_solution(Cols, N),               % Solve N-Queens for given N
        format(atom(FileName), 'queens~w.json', [N]), % Dynamic filename: queenN.json
        write_json(FileName, Cols),                % Export solution to JSON
        format('Wrote ONE solution for N=~w to ~w~n', [N, FileName])
    ; format('Please provide N as argument.~n')
    ),
    halt.

% --- Core solver --------------------------------------------------------------
% solve_one_solution(-Cols, +N)
% Cols is a list of column positions for each row (solution representation).
solve_one_solution(Cols, N) :-
    length(Cols, N),                % Create a list of N variables
    Cols ins 1..N,                  % Each queen is in a column between 1 and N
    all_different(Cols),            % No two queens share the same column
    numlist(1, N, Rows),            % Generate row indices [1..N]
    maplist(sum_with_index, Cols, Rows, SumDiag),  % Diagonal sums
    maplist(diff_with_index, Cols, Rows, DiffDiag),% Diagonal differences
    all_different(SumDiag),         % No two queens share same diagonal (sum)
    all_different(DiffDiag),        % No two queens share same diagonal (difference)
    labeling([ff], Cols).           % Search for a solution using first-fail heuristic

% Helper predicates for diagonal constraints
sum_with_index(Qi, I, S)  :- S #= Qi + I.
diff_with_index(Qi, I, D) :- D #= Qi - I.

% --- JSON export --------------------------------------------------------------
% positions_dicts(+Cols, -PosDicts)
% Converts solution list into a list of row/column dictionaries.
positions_dicts(Cols, PosDicts) :-
    length(Cols, N),
    numlist(1, N, Rows),
    maplist(row_col_dict, Rows, Cols, PosDicts).

row_col_dict(R, C, _{row:R, col:C}).

% write_json(+File, +Cols)
% Writes the solution to a JSON file with structure:
% {
%   "n": N,
%   "solution": [ {row:1, col:4}, {row:2, col:2}, ... ]
% }
write_json(File, Cols) :-
    positions_dicts(Cols, PosDicts),
    length(Cols, N),
    Dict = _{ n:N, solution:PosDicts },
    setup_call_cleanup(
        open(File, write, S, [encoding(utf8)]),
        json_write_dict(S, Dict, [width(0), indent(2)]),
        close(S)
    ).
