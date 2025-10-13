%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% KNOWLEDGE BASE
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% path_oneway(City1, City2, Cost)
% Defines the cost (distance) of traveling between two adjacent cities in one direction.
path_oneway(arad, zerind, 75).
path_oneway(arad, sibiu, 140).
path_oneway(arad, timisoara, 118).
path_oneway(bucharest, fagaras, 211).
path_oneway(bucharest, pitesti, 101).
path_oneway(bucharest, giurgiu, 90).
path_oneway(bucharest, urziceni, 85).
path_oneway(craiova, drobeta, 120).
path_oneway(craiova, rimnicu_vilcea, 146).
path_oneway(craiova, ganeasa, 47). % Using your added city
path_oneway(drobeta, mehadia, 75).
path_oneway(eforie, hirsova, 86).
path_oneway(fagaras, sibiu, 99).
path_oneway(hirsova, urziceni, 98).
path_oneway(iasi, vaslui, 92).
path_oneway(iasi, neamt, 87).
path_oneway(lugoj, timisoara, 111).
path_oneway(lugoj, mehadia, 70).
path_oneway(oradea, zerind, 71).
path_oneway(oradea, sibiu, 151).
path_oneway(pitesti, rimnicu_vilcea, 97).
path_oneway(rimnicu_vilcea, sibiu, 80).
path_oneway(rimnicu_vilcea, ganeasa, 84). % Using your added city
path_oneway(urziceni, vaslui, 142).

% path(CityA, CityB, Cost)
% This rule makes the paths bidirectional, so we don't have to define them twice.
path(A, B, C) :- path_oneway(A, B, C).
path(A, B, C) :- path_oneway(B, A, C).

% h(City, HeuristicCost)
% Heuristic function h(n): estimated (straight-line) distance from City to Bucharest.
h(arad, 366).
h(bucharest, 0).
h(craiova, 160).
h(drobeta, 242).
h(eforie, 161).
h(fagaras, 176).
h(ganeasa, 150).  % Estimated heuristic for your new city, placed near Craiova.
h(giurgiu, 77).
h(hirsova, 151).
h(iasi, 226).
h(lugoj, 244).
h(mehadia, 241).
h(neamt, 234).
h(oradea, 380).
h(pitesti, 100).
h(rimnicu_vilcea, 193).
h(sibiu, 253).
h(timisoara, 329).
h(urziceni, 80).
h(vaslui, 199).
h(zerind, 374).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% A* ALGORITHM LOGIC
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% a_star(Start, Goal, Path, Cost)
% This is the main predicate to call. It initializes the open list
% with the starting node and calls the recursive search predicate.
a_star(Start, Goal, Path, Cost) :-
    h(Start, H),
    % The initial node has a g(n) of 0. Its f(n) is just its h(n).
    Open = [f(H, 0, H, Start, [Start])],
    Closed = [],
    search(Open, Closed, Goal, Path, Cost).

% --- Search Predicate ---

% Base Case: Goal is Reached.
% If the node at the head of the Open list is the goal, we've found the optimal path.
search([f(_, G, _, Goal, Path)|_], _, Goal, ReversedPath, G) :-
    reverse(Path, ReversedPath). % Reverse the path for correct order

% Recursive Step: Expand the Best Node.
search([CurrentNode|RestOpen], Closed, Goal, FinalPath, FinalCost) :-
    % Extract the state (city) from the current node
    CurrentNode = f(_, _, _, Current, _),
    
    % If we have already visited this state, ignore it and continue with the rest of the open list.
    (   member(Current, Closed) ->
        search(RestOpen, Closed, Goal, FinalPath, FinalCost)
    ;
    % Otherwise, find all successors
        findall(
            Successor,
            generate_successor(CurrentNode, Successor),
            Successors
        ),
        
        % Add the current state to the closed list
        NewClosed = [Current|Closed],
        
        % Merge new successors with the rest of the open list
        append(RestOpen, Successors, NewOpenUnsorted),
        
        % Sort the new open list by F-cost to ensure the best node is always processed next
        sort_open_list(NewOpenUnsorted, NewOpen),
        
        % Continue the search
        search(NewOpen, NewClosed, Goal, FinalPath, FinalCost)
    ).

% --- Helper Predicates ---

% generate_successor(+CurrentNode, -SuccessorNode)
% Finds an adjacent city and creates a full successor node record.
generate_successor(f(_, G, _, Current, Path), f(F_succ, G_succ, H_succ, Succ, [Succ|Path])) :-
    path(Current, Succ, StepCost),
    % Ensure the successor is not already in the current path to avoid cycles
    \+ member(Succ, Path),
    % Calculate the new g(n)
    G_succ is G + StepCost,
    % Look up the h(n)
    h(Succ, H_succ),
    % Calculate the new f(n)
    F_succ is G_succ + H_succ.

% sort_open_list(+List, -SortedList)
% Sorts the open list based on F-cost (the first argument of the f/5 term).
sort_open_list(List, Sorted) :-
    predsort(compare_f_values, List, Sorted).

% compare_f_values(?Order, +Term1, +Term2)
% A custom comparator for predsort. It tells Prolog how to order two f/5 terms.
compare_f_values(Order, f(F1,_,_,_,_), f(F2,_,_,_,_)) :-
    ( F1 < F2 -> Order = (<)
    ; F1 > F2 -> Order = (>)
    ; Order = (=)
    ).