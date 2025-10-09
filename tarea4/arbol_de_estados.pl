% Definición del Espacio de Estados

sucesor(N, M) :-
    M is 2 * N,      % Primera regla sucesora
    M =< 15.         % Condición de límite

sucesor(N, M) :-
    M is 2 * N + 1,  % Segunda regla sucesora
    M =< 15.         % Condición de límite

% árbol recursivo
arbol(N, tree(N, Hijos)) :-
    findall(SubArbol, 
            (sucesor(N, M), arbol(M, SubArbol)), 
            Hijos).

