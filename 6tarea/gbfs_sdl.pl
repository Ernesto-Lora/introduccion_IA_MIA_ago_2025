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
path_oneway(craiova, ganeasa, 47).
path_oneway(craiova, pitesti, 138).
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
path_oneway(pitesti, rimnicu_vilcea, 97). %%%%%%%%%
path_oneway(rimnicu_vilcea, sibiu, 80).
path_oneway(rimnicu_vilcea, ganeasa, 84).
path_oneway(urziceni, vaslui, 142).

% path(CityA, CityB, Cost)
% This rule makes the paths bidirectional, so we don't have to define them twice.
path(A, B, C) :- path_oneway(A, B, C).
path(A, B, C) :- path_oneway(B, A, C).

% Straigth line distance to Fagaras
h(arad, 218).
h(bucharest, 154).
h(craiova, 169).
h(drobeta, 205). %%%%%%%%
h(eforie, 300).
h(fagaras, 0).
h(giurgiu, 192).
h(hirsova, 249).
h(iasi, 177).
h(lugoj, 156).
h(mehadia, 175).
h(neamt, 133).
h(oradea, 212).
h(pitesti, 82). %%%%%%%
h(rimnicu_vilcea, 81). %%%%%%%%%
h(sibiu, 98). %%%%%%%%%%
h(timisoara, 214).
h(urziceni, 180).
h(vaslui, 204).
h(zerind, 213).
h(ganeasa, 103). %%%%%%%%


% Greedy Best-First Search (GBFS) Implementation


% Main GBFS call
% Finds a path from Start to Goal using a straight-line distance heuristic.
% Returns the Path and its TotalCost.
gbfs_sdl(Start, Goal, Path, TotalCost) :-
    % Get the heuristic value for the starting city.
    h(Start, H),
    % The initial queue contains one item:
    % The heuristic H, the starting cost 0, and the starting path [Start].
    % Format: [Heuristic - (Cost - Path)]
    InitialQueue = [H - (0 - [Start])],
    % Start the search with the initial priority queue.
    gbfs_queue(InitialQueue, Goal, RevPath, TotalCost),
    % Reverse the path to get the correct order (Start -> Goal).
    reverse(RevPath, Path).

% ---

% Base case: Goal found 
% The path at the head of the priority queue ends with the Goal.
% We have found the solution.
gbfs_queue([_H - (Cost - [Goal|RestPath]) | _], Goal, [Goal|RestPath], Cost).

% ---

% Recursive case: Expand the best path and continue the search
gbfs_queue([_H - (CurrentCost - CurrentPath) | OtherPaths], Goal, FinalPath, FinalCost) :-
    % CurrentPath is [CurrentCity | ... ], get the head.
    CurrentPath = [CurrentCity|_],

    % Find all valid successor paths and package them for the priority queue.
    findall(NextH - (NewCost - [NextCity|CurrentPath]),
            (
             % 1. Find an adjacent city and the cost of the step.
             path(CurrentCity, NextCity, StepCost),
             % 2. Ensure NextCity hasn't been visited (no cycles).
             \+ member(NextCity, CurrentPath),
             % 3. Calculate the new accumulated cost for this new path.
             NewCost is CurrentCost + StepCost,
             % 4. Look up the heuristic value for the new city.
             h(NextCity, NextH)
            ),
            NewChildren), % This list contains all the new Heuristic-(Cost-Path) pairs.

    % Add the newly found children to the rest of the queue.
    append(OtherPaths, NewChildren, CombinedQueue),

    % Sort the queue by the heuristic value.
    keysort(CombinedQueue, UpdatedQueue),

    % Recurse with the newly sorted priority queue.
    gbfs_queue(UpdatedQueue, Goal, FinalPath, FinalCost).

% Failure case: The queue is empty, but the Goal was not found.
gbfs_queue([], _Goal, [], -1) :-
    write('Path not found.'), nl.