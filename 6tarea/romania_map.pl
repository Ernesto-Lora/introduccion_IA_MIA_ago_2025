/*
  =============================================================================
  Romania Map Search - Depth-First Search with Heuristic Support
  -----------------------------------------------------------------------------

  This Prolog program performs a depth-first search (DFS) on a simplified map
  of Romania. It includes support for calculating and storing straight-line
  distances (SLD) between cities as a heuristic, useful for informed search
  algorithms like A* or Greedy Best-First Search.

  -----------------------------------------------------------------------------
  USAGE: 

    ?- search(StartCity, GoalCity).

    - Performs a DFS from StartCity to GoalCity.
    - Prints the path found and the total cost of the route.
    - Example:
        ?- search(arad, bucharest).
        Output:
          Found Path: [arad, sibiu, fagaras, bucharest]
          Total Cost: 450

  -----------------------------------------------------------------------------
  HEURISTIC (SLD) DISTANCES:

    ?- generate_sld(GoalCity).

    - Calculates and asserts sld(City, GoalCity, Distance) facts into memory.
    - These represent the straight-line (Euclidean) distance from each city
      to the specified GoalCity.
    - Example:
        ?- generate_sld(bucharest).
        Asserts facts like:
          sld(arad, bucharest, 702).
          sld(sibiu, bucharest, 466).
          ...

    - To view all SLD facts toward a goal:
        ?- sld(X, bucharest, D).
    
    - Also, after running, search(arad, bucharest).
        ?- print_all_slds.

  -----------------------------------------------------------------------------
  NOTES:

    - The map is undirected: connections between cities are bidirectional.
    - Distances between cities are based on predefined road costs.
    - sld/3 facts are dynamic and stored in memory using assert/1.
    - Re-running generate_sld/1 without clearing previous facts may cause
      duplicates. Use:
          ?- retractall(sld(_, Goal, _)).
      to remove existing facts before regenerating them.
    - print_all_slds can be run after running a searhc, or asserting a Goal.

  =============================================================================
*/

:- dynamic sld/3.

% Map and Coordinates Dictionaries
map(romania{
    romania_map: _{
        arad: _{zerind:75, sibiu:140, timisoara:118},
        bacau: _{neamt:66, urziceni:240},
        brasov: _{fagaras:66, neamt:232, ploiesti:111},
        bucharest: _{fagaras:211, giurgiu:90, pitesti:101, ploiesti:79, urziceni:85},
        craiova: _{drobeta:120, ganeasa:47, rimnicu:146, pitesti:138},
        drobeta: _{mehadia:75, craiova:120},
        eforie: _{hirsova:86},
        fagaras: _{brasov:66, sibiu:99, bucharest:211},
        ganeasa: _{rimnicu:84, craiova:47},
        giurgiu: _{bucharest:90},
        hirsova: _{urziceni:98, eforie:86},
        iasi: _{vaslui:92, neamt:87},
        lugoj: _{timisoara:111, mehadia:70},
        mehadia: _{lugoj:70, drobeta:75},
        neamt: _{iasi:87, bacau:66, brasov:232},
        oradea: _{zerind:71, sibiu:151},
        pitesti: _{rimnicu:97, craiova:138, bucharest:101},
        ploiesti: _{brasov:111, bucharest:79},
        rimnicu: _{ganeasa:84, sibiu:80, pitesti:97, craiova:146},
        sibiu: _{arad:140, fagaras:99, oradea:151, rimnicu:80},
        timisoara: _{arad:118, lugoj:111},
        urziceni: _{bacau:240, bucharest:85, vaslui:142, hirsova:98},
        vaslui: _{urziceni:142, iasi:92},
        zerind: _{arad:75, oradea:71}
    },
    locations: _{
        arad:[183,987], bacau:[896,973], bucharest:[802,655], brasov:[721,871],
        craiova:[507,577], drobeta:[331,598], eforie:[1125,587], fagaras:[611,900],
        ganeasa:[521,612], giurgiu:[752,541], hirsova:[1071,702], iasi:[950,1015],
        lugoj:[331,764], mehadia:[336,673], neamt:[812,1075], oradea:[263,1146],
        pitesti:[642,738], ploiesti:[755,748], rimnicu:[468,823], sibiu:[416,916],
        timisoara:[188,823], urziceni:[912,702], vaslui:[1020,889], zerind:[216,1069]
    }
}).

% Calculate Euclidean distance
distance([X1,Y1],[X2,Y2], Dint) :-
    DX is X1 - X2,
    DY is Y1 - Y2,
    D is sqrt(DX*DX + DY*DY),
    Dint is integer(D).  % No decimals

% SLD to Goal from all the cities
generate_sld(Goal) :-
    retractall(sld(_, Goal, _)),  % Clean Previous Duplicates
    map(M),
    Locs = M.locations,
    dict_keys(Locs, Cities),
    member(Goal, Cities),
    forall(member(C, Cities),
           (   ( C = Goal ->
                   D = 0
               ;   CoordC = Locs.get(C),
                   CoordG = Locs.get(Goal),
                   distance(CoordC, CoordG, D)
               ),
               assert(sld(C, Goal, D))
           )).
            
% Print all cities and SLD to Goal
print_all_slds :-
    sld(_, Goal,_),!,
    findall([City, Goal, Dist], sld(City, Goal, Dist), List),
    forall(member([C, G, D], List),
           format('~w -> ~w = ~w~n', [C, G, D])).
            
% Check edges between cities
edge(X, Y, Cost) :-
    map(M),
    Map = M.romania_map,
    (   get_dict(X, Map, SubMap), get_dict(Y, SubMap, Cost)
    ;   get_dict(Y, Map, SubMap2), get_dict(X, SubMap2, Cost)
    ).

% Depth-First search
path(Node, Node, _, [Node], 0).
path(Start, Finish, Visited, [Start | Path], TotalCost) :-
    edge(Start, Next, Cost),
    \+ member(Next, Visited),
    path(Next, Finish, [Next | Visited], Path, RestCost),
    TotalCost is Cost + RestCost.

% Calling Predicate
search(Start, Goal) :-
    generate_sld(Goal),
    path(Start, Goal, [Start], Path, TotalCost),
    format('Found Path: ~w~n', [Path]),
    format('Total Cost: ~w~n', [TotalCost]), !.


% Iterative Deepening Search (IDS)

% Punto de entrada del algoritmo IDS
ids(Inicio, Objetivo, Solucion) :-
    % Llamar a la búsqueda iterativa con profundidad inicial 0
    iterative_deepening(Inicio, Objetivo, 0, Solucion).

% Bucle de profundización iterativa
iterative_deepening(Inicio, Objetivo, Profundidad, Solucion) :-
    % Llamada a búsqueda limitada por profundidad con corte
    depth_limited_search(Inicio, Objetivo, Profundidad, [Inicio], Solucion), !.

iterative_deepening(Inicio, Objetivo, Profundidad, Solucion) :-
    % Incrementar profundidad y repetir búsqueda
    NuevaProfundidad is Profundidad + 1,
    iterative_deepening(Inicio, Objetivo, NuevaProfundidad, Solucion).

% Búsqueda limitada por profundidad (Caso Base: Objetivo encontrado)
% El esqueleto original fue ajustado para seguir el patrón de path/5
depth_limited_search(Nodo, Objetivo, _, _, [Nodo]) :-
    Nodo == Objetivo.

% Búsqueda limitada por profundidad (Caso Recursivo)
depth_limited_search(Nodo, Objetivo, Profundidad, Visitados, [Nodo|Solucion]) :-
    % Verificar que la profundidad sea mayor a 0
    Profundidad > 0,
    % Obtener nodos adyacentes (costo no importa para IDS)
    edge(Nodo, Siguiente, _),
    % Evitar ciclos
    \+ member(Siguiente, Visitados),
    % Llamar recursivamente con profundidad reducida
    NuevaProfundidad is Profundidad - 1,
    depth_limited_search(Siguiente, Objetivo, NuevaProfundidad, [Siguiente|Visitados], Solucion).

% Greedy Best-First Search
% Greedy utiliza la heurística sld/3 para elegir el nodo más prometedor:
% Punto de entrada del algoritmo Greedy Best-First Search
% La frontera almacenará pares: [[Camino], Heurística]

gbfs(Inicio, Objetivo, Solucion) :-
    % Generar los valores de SLD (h(n)) para el objetivo
    generate_sld(Objetivo), 
    heuristica(Inicio, H),
    
    % La frontera almacena [[Camino], Heuristica]
    % 1. Llama al ciclo principal. Usamos 'SolucionReversa' 
    %    para clarificar que el camino viene al revés.
    gbfs_loop([[[Inicio], H]], Objetivo, [], SolucionReversa),
    
    % 2. Invierte la lista para obtener el orden [Inicio, ..., Objetivo]
    reverse(SolucionReversa, Solucion).



% Ciclo principal de búsqueda (Caso Base: Objetivo encontrado)
% El esqueleto fue modificado para devolver el camino completo
gbfs_loop([[[Nodo|Camino], _]|_], Objetivo, _, [Nodo|Camino]) :-
    % Condición de éxito si Nodo es el objetivo.
    Nodo == Objetivo.

% Ciclo principal de búsqueda (Caso Recursivo)
gbfs_loop([[[Nodo|Camino], _]|RestoFrontera], Objetivo, Visitados, Solucion) :-
    % Verificar que Nodo no esté en Visitados
    \+ member(Nodo, Visitados),
    % Obtener vecinos con heurística
    findall([[V, Nodo|Camino], HV],
            (adjacent(Nodo, V), \+ member(V, Visitados), heuristica(V, HV)),
            VecinosConH),
    % Insertar vecinos en la frontera ordenada por heurística
    append(VecinosConH, RestoFrontera, TempFrontera),
    predsort(compara_gbfs_f, TempFrontera, NuevaFrontera),
    % Llamar recursivamente con nueva frontera y Visitados actualizado
    gbfs_loop(NuevaFrontera, Objetivo, [Nodo|Visitados], Solucion).

% Caso recursivo si el nodo ya fue visitado (descartar y continuar)
gbfs_loop([_|RestoFrontera], Objetivo, Visitados, Solucion) :-
    gbfs_loop(RestoFrontera, Objetivo, Visitados, Solucion).

% Helper para ordenar la frontera de GBFS por H
compara_gbfs_f(Delta, [_, H1], [_, H2]) :-
    (H1 =< H2 -> Delta = '<' ; Delta = '>').

% Heurística (usa los hechos sld/3 generados)
heuristica(Nodo, Valor) :-
    % Obtiene la heurística (SLD) para el Nodo hacia el Objetivo (implícito en sld/3)
    sld(Nodo, _, Valor), !.

% Grafo (usa el predicado edge/3 existente)
adjacent(Nodo, Vecino) :-
    % Definir conexiones entre nodos (costo no es necesario para GBFS)
    edge(Nodo, Vecino, _).

% A* Search
% A* combina el costo acumulado g(n) con la heurística h(n):
% Punto de entrada del algoritmo A*
% La frontera almacenará tripletas: [[Camino], CostoG, HeurísticaH]
astar(Inicio, Objetivo, Solucion) :-
    % Generar los valores de SLD (h(n)) para el objetivo
    generate_sld(Objetivo),
    heuristica(Inicio, H),
    
    % 1. Llama al ciclo principal.
    %    Este nos dará [ [Objetivo,...,Inicio], CostoTotal ]
    astar_loop([[[Inicio], 0, H]], Objetivo, [], [CaminoReverso, CostoTotal]),
    
    % 2. Invertimos solo la lista del camino
    reverse(CaminoReverso, CaminoCorrecto),
    
    % 3. Empaquetamos la solución final con el camino correcto y el costo
    Solucion = [CaminoCorrecto, CostoTotal].

% Ciclo principal de búsqueda (Caso Base: Objetivo encontrado)
astar_loop([[[Nodo|Camino], CostoG, _]|_], Objetivo, _, [[Nodo|Camino], CostoG]) :-
    % Condición de éxito si Nodo es el objetivo.
    Nodo == Objetivo.

% Ciclo principal de búsqueda (Caso Recursivo)
astar_loop([[[Nodo|Camino], CostoG, _]|RestoFrontera], Objetivo, Visitados, Solucion) :-
    % Verificar que Nodo no esté en Visitados
    \+ member(Nodo, Visitados),
    % Obtener vecinos y calcular g(n) y h(n)
    findall([[V, Nodo|Camino], NuevoG, HV],
            (adjacent(Nodo, V, CostoArco),
             \+ member(V, Visitados),
             NuevoG is CostoG + CostoArco,
             heuristica(V, HV)),
            VecinosInfo),
    % Insertar vecinos en la frontera ordenada por f(n) = g(n) + h(n)
    append(VecinosInfo, RestoFrontera, TempFrontera),
    predsort(compara_astar_f, TempFrontera, NuevaFrontera),
    % Llamar recursivamente con nueva frontera y Visitados actualizado
    astar_loop(NuevaFrontera, Objetivo, [Nodo|Visitados], Solucion).

% Caso recursivo si el nodo ya fue visitado (descartar y continuar)
astar_loop([_|RestoFrontera], Objetivo, Visitados, Solucion) :-
    astar_loop(RestoFrontera, Objetivo, Visitados, Solucion).

% Helper para ordenar la frontera de A* por F = G + H
compara_astar_f(Delta, [_, G1, H1], [_, G2, H2]) :-
    F1 is G1 + H1,
    F2 is G2 + H2,
    (F1 =< F2 -> Delta = '<' ; Delta = '>').

% Heurística (usa los hechos sld/3 generados)
heuristica(Nodo, Valor) :-
    % Definir cómo se calcula la heurística h(n)
    sld(Nodo, _, Valor), !.

% Grafo con costos (usa el predicado edge/3 existente)
adjacent(Nodo, Vecino, Costo) :-
    % Definir conexiones entre nodos y su costo g(n)
    edge(Nodo, Vecino, Costo).
