import socket
import threading
import json
import uuid
from typing import Dict, Set, Any

# Para correr con la topología del ejemplo:
# python router_flooding.py topo.json A
# python router_flooding.py topo.json B
# python router_flooding.py topo.json C
# python router_flooding.py topo.json D


# Configuración global
HOST = "127.0.0.1"
BASE_PORT = 1235  # puerto base (A=1235, B=1236, C=1237, ...)


# Cargar topología
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


# Crear paquete JSON
def make_packet(src: str, dst: str, ttl: int, payload: str) -> Dict[str, Any]:
    return {
        "proto": "flooding",
        "type": "message",
        "from": src,
        "to": dst,
        "ttl": ttl,
        "headers": [{"id": str(uuid.uuid4())}],
        "payload": payload
    }


# Router con flooding
class FloodingRouter:
    def __init__(self, node: str, graph: Dict[str, Dict[str, float]]):
        self.node = node
        self.graph = graph
        self.port = BASE_PORT + (ord(node) - ord("A"))  # asignar puerto según letra
        self.seen_packets: Set[str] = set()  # evitar duplicados

    # Servidor que escucha conexiones entrantes
    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((HOST, self.port))
        server_socket.listen(5)
        print(f"[{self.node}] Router escuchando en {HOST}:{self.port}")

        while True:
            client_socket, addr = server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    # Manejar paquetes recibidos
    def handle_client(self, client_socket: socket.socket):
        data = client_socket.recv(4096).decode("utf-8")
        if not data:
            client_socket.close()
            return

        packet = json.loads(data)
        pkt_id = packet["headers"][0]["id"]

        if pkt_id in self.seen_packets:
            print(f"[{self.node}] Paquete duplicado {pkt_id}, descartado")
            client_socket.close()
            return
        self.seen_packets.add(pkt_id)

        # Decrementar TTL
        packet["ttl"] -= 1
        if packet["ttl"] <= 0:
            print(f"[{self.node}] TTL agotado para paquete {pkt_id}, descartado")
            client_socket.close()
            return

        # Verificar si soy el destino
        if packet["to"] == self.node:
            print(f"[{self.node}] Recibí mensaje: {packet['payload']}")
        else:
            # Reenviar a vecinos
            for neigh in self.graph[self.node]:
                neigh_port = BASE_PORT + (ord(neigh) - ord("A"))
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.connect((HOST, neigh_port))
                        s.send(json.dumps(packet).encode("utf-8"))
                        print(f"[{self.node}] reenviando paquete {pkt_id} a {neigh}")
                except ConnectionRefusedError:
                    print(f"[{self.node}] No pude conectar con {neigh} (caído)")

        client_socket.close()

    # Enviar un paquete inicial
    def send_packet(self, dst: str, payload: str, ttl: int = 5):
        packet = make_packet(self.node, dst, ttl, payload)
        # Enviar a todos mis vecinos
        for neigh in self.graph[self.node]:
            neigh_port = BASE_PORT + (ord(neigh) - ord("A"))
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((HOST, neigh_port))
                    s.send(json.dumps(packet).encode("utf-8"))
                    print(f"[{self.node}] enviando paquete inicial a {neigh}")
            except ConnectionRefusedError:
                print(f"[{self.node}] No pude conectar con {neigh} (caído)")


# Ejemplo de ejecución
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Uso: python router_flooding.py <topo.json> <Nodo>")
        sys.exit(1)

    topo_path = sys.argv[1]
    node = sys.argv[2]

    graph = load_topology(topo_path)
    router = FloodingRouter(node, graph)

    # Servidor en un hilo
    threading.Thread(target=router.start_server, daemon=True).start()

    # Si es nodo origen, mandar mensaje de prueba
    if node == "A":  # origen
        import time
        time.sleep(1)  # esperar a que todos levanten
        router.send_packet("D", "Hola desde A con Flooding!", ttl=5)

    # Mantener vivo
    while True:
        pass
