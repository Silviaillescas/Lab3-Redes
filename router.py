import socket
import threading
import json
import heapq
from typing import Dict, List, Tuple, Optional

# Variables globales para la dirección y puerto del router
HOST = '127.0.0.1'  # Dirección IP del router
PORT = 12345         # Puerto de escucha

# Carga de topología (como en tu código anterior)
def load_topology(path: str) -> Dict[str, Dict[str, float]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cfg = data.get("config", {})
    graph: Dict[str, Dict[str, float]] = {}
    for u, neigh in cfg.items():
        if isinstance(neigh, dict):
            graph[u] = {v: float(w) for v, w in neigh.items()}
        else:
            graph[u] = {v: 1.0 for v in neigh}
    for u in list(cfg.keys()):
        graph.setdefault(u, {})
    return graph

# Implementación de Dijkstra
def dijkstra(graph: Dict[str, Dict[str, float]], source: str) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
    INF = float("inf")
    dist = {v: INF for v in graph}
    prev: Dict[str, Optional[str]] = {v: None for v in graph}
    dist[source] = 0.0
    pq: List[Tuple[float, str]] = [(0.0, source)]

    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, w in graph[u].items():
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    return dist, prev

# Manejo de forwarding
def forward_packet(destination: str, graph: Dict[str, Dict[str, float]], source: str) -> str:
    dist, prev = dijkstra(graph, source)
    path = []
    cur = destination
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()

    # El primer nodo después del origen es el siguiente salto
    next_hop = path[1] if len(path) > 1 else None
    return next_hop

# Función para manejo de conexiones y forwarding de paquetes
def handle_client(client_socket: socket.socket, graph: Dict[str, Dict[str, float]], source: str) -> None:
    data = client_socket.recv(1024).decode('utf-8')  # Recibe el paquete (por ejemplo, la dirección de destino)
    print(f"Paquete recibido para el destino: {data}")
    
    # Procesar el paquete
    next_hop = forward_packet(data, graph, source)

    # Enviar al siguiente salto (si existe)
    if next_hop:
        client_socket.send(f"Paquete reenviado a {next_hop}".encode('utf-8'))
    else:
        client_socket.send("No hay ruta al destino".encode('utf-8'))
    
    client_socket.close()

# Servidor principal del router
def router_server(graph: Dict[str, Dict[str, float]], source: str) -> None:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)

    print(f"Router {source} escuchando en {HOST}:{PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Conexión aceptada de {client_address}")

        # Crear un hilo para manejar la conexión (forwarding)
        client_thread = threading.Thread(target=handle_client, args=(client_socket, graph, source))
        client_thread.start()

# Función principal de ejecución
if __name__ == "__main__":
    topo_path = 'topo.json'  # Ruta del archivo de topología
    source_router = 'A'      # El nombre del router origen

    graph = load_topology(topo_path)  # Cargar topología

    # Ejecutar el servidor en un hilo para enrutamiento y forwarding en paralelo
    router_thread = threading.Thread(target=router_server, args=(graph, source_router))
    router_thread.start()
