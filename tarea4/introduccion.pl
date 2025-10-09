padre(juan,maria).
% juan es padre de maria
padre(juan,pedro).
% juan es padre de pedro

padre(lili,juan).
padre(ernesto,juan).


abuelo(X,Y) :- padre(X,Z), padre(Z,Y).
% X es el abuelo de Y si: X es el padre de Z y Z es el padre de Y

sucesor(X,Y):- Y is 2*X.
sucesor(X,Y):- Y is 2*X + 1.