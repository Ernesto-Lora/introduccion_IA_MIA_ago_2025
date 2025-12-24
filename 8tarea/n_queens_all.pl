/*
   N_Queens in Prolog (All Solutions) with JSON export
   ---------------------------------------------------
   - Solves ALL solutions for a given N using findall.
   - Exports the solutions to a JSON file named queens<N>_all.json.
   - Usage:
       swipl -q -s n_queens_all.pl -- 8
*/

:- use_module(library(clpfd)).        % Constraint Logic Programming
:- use_module(library(http/json)).    % JSON read/write support
:- initialization(main, main).

% --- Main entry point ---------------------------------------------------------
main :-
    current_prolog_flag(argv, Argv),
    ( Argv = [NAtom|_] ->
        atom_number(NAtom, N),
        
        format('Solving for N=~w...~n', [N]),
        
        % Find ALL solutions using findall/3
        % This collects every valid 'Cols' list into 'AllCols'
        findall(Cols, solve_one_solution(Cols, N), AllCols),
        
        length(AllCols, Count),
        format('Found ~w solutions.~n', [Count]),

        % 2. Generate filename and write JSON
        format(atom(FileName), 'queens~w_all.json', [N]),
        write_json(FileName, N, AllCols),
        
        format('Saved all solutions to ~w~n', [FileName])
    ; 
        format('Please provide N as argument (e.g., swipl ... -- 8).~n')
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


% Helper predicates for diagonals
sum_with_index(Qi, I, S)  :- S #= Qi + I.
diff_with_index(Qi, I, D) :- D #= Qi - I.

% --- JSON export --------------------------------------------------------------

% write_json(+File, +N, +AllCols)
% Writes the final JSON structure.
write_json(File, N, AllCols) :-
    % Transform the list of simple lists [[1,5...], [2,6...]] 
    % into a list of formatted dictionaries.
    maplist(solution_to_dicts, AllCols, AllSolutionsFormatted),
    
    % Create the top-level object
    FinalJSON = _{
        n: N,
        solutions: AllSolutionsFormatted
    },
    
    setup_call_cleanup(
        open(File, write, S, [encoding(utf8)]),
        json_write_dict(S, FinalJSON, [width(0), indent(2)]),
        close(S)
    ).

% solution_to_dicts(+Cols, -PosDicts)
% Converts a SINGLE solution (list of integers) into a list of row/col dicts.
solution_to_dicts(Cols, PosDicts) :-
    length(Cols, N),
    numlist(1, N, Rows),
    maplist(row_col_dict, Rows, Cols, PosDicts).

% row_col_dict(+Row, +Col, -Dict)
% Creates the small object {"col": C, "row": R}
row_col_dict(R, C, _{col:C, row:R}).