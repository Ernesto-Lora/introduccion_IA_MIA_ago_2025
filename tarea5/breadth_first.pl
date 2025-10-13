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


% Main BFS call
% Find path from Start to Goal
bfs(Start, Goal, Path) :-
    % Start the search with a queue containing only the initial path: [[Start]]
    bfs_queue([[Start]], Goal, RevPath),
    reverse(RevPath, Path).

% Base case: Goal found 
% The current path's head is the Goal, so this path is the solution.
bfs_queue([ [Goal|RestPath] | _], Goal, [Goal|RestPath]).


% Recursive case: Expand the first path and continue BFS
bfs_queue([CurrentPath|OtherPaths], Goal, FinalPath) :-
    % CurrentPath is a list: [CurrentCity, ... , StartCity]
    CurrentPath = [CurrentCity|_],

    % findall/3: Find all unvisited neighbors (NextCity) of CurrentCity.
    % It creates a new path [NextCity|CurrentPath] for each valid neighbor.
    findall([NextCity|CurrentPath],
            (
             % 1. Find an adjacent city using the path/3 predicate, ignoring the cost (with '_')
             path(CurrentCity, NextCity, _),
             % 2. Ensure NextCity hasn't been visited in the current path (no cycles)
             \+ member(NextCity, CurrentPath)
            ),
            NewPaths),

    % Add all NewPaths (the "children" of CurrentPath) to the end of the queue.
    % This is the key operation for Breadth-First Search (FIFO queue).
    append(OtherPaths, NewPaths, UpdatedQueue),

    % Recurse with the UpdatedQueue
    bfs_queue(UpdatedQueue, Goal, FinalPath).