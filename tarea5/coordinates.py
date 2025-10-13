import matplotlib.pyplot as plt

# --- Mapa de Rumania ---
romania_map = dict(
    Arad=dict(Zerind=75, Sibiu=140, Timisoara=118),
    Bucharest=dict(Urziceni=85, Pitesti=101, Giurgiu=90, Fagaras=211),
    Craiova=dict(Drobeta=120, Rimnicu=146, Pitesti=138),
    Drobeta=dict(Mehadia=75),
    Eforie=dict(Hirsova=86),
    Fagaras=dict(Sibiu=99),
    Hirsova=dict(Urziceni=98),
    Iasi=dict(Vaslui=92, Neamt=87),
    Lugoj=dict(Timisoara=111, Mehadia=70),
    Oradea=dict(Zerind=71, Sibiu=151),
    Pitesti=dict(Rimnicu=97),
    Rimnicu=dict(Sibiu=80),
    Urziceni=dict(Vaslui=142),
    Ganeasa=dict(Rimnicu=84, Craiova=47)
)

# --- Movimiento bidireccional ---
grafo_bidireccional = {}
for ciudad, vecinos in romania_map.items():
    grafo_bidireccional.setdefault(ciudad, {})
    for vecino, dist in vecinos.items():
        grafo_bidireccional[ciudad][vecino] = dist
        grafo_bidireccional.setdefault(vecino, {})
        if ciudad not in grafo_bidireccional[vecino]:
            grafo_bidireccional[vecino][ciudad] = dist

# --- Coordenadas ---
locations = dict(
    Arad=(91, 492), Bucharest=(400, 327), Craiova=(253, 288),
    Drobeta=(165, 299), Eforie=(562, 293), Fagaras=(305, 449),
    Giurgiu=(375, 270), Hirsova=(534, 350), Iasi=(473, 506),
    Lugoj=(165, 379), Mehadia=(168, 339), Neamt=(406, 537),
    Oradea=(131, 571), Pitesti=(320, 368), Rimnicu=(233, 410),
    Sibiu=(207, 457), Timisoara=(94, 410), Urziceni=(456, 350),
    Vaslui=(509, 444), Zerind=(108, 531), Ganeasa=(275, 350)
)


# --- Dibujar mapa ---
plt.figure(figsize=(12, 9))
ax = plt.gca()

# Dibujar conexiones entre ciudades
for city, neighbors in grafo_bidireccional.items():
    for neighbor in neighbors:
        x_values = [locations[city][0], locations[neighbor][0]]
        y_values = [locations[city][1], locations[neighbor][1]]
        ax.plot(x_values, y_values, 'k-', lw=1, alpha=0.3)

# Dibujar ciudades
for city, (x, y) in locations.items():
    ax.plot(x, y, 'ro', markersize=8)
    ax.text(x + 5, y + 5, city, fontsize=9)

ax.set_title("Mapa de Rumania")
ax.grid(True)
ax.set_xlabel("X")
ax.set_ylabel("Y")

plt.show()