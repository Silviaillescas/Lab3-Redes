import json
import sys
import uuid
from typing import Dict, List, Set, Any
# Para correrlo con la topología del ejemplo:
# python flooding_rt.py topo.json A D


# Cargar la topología
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
def make_packet(proto: str, ptype: str, src: str, dst: str, ttl: int, payload: str) -> Dict[str, Any]:
    return {
        "proto": proto,
        "type": ptype,
        "from": src,
        "to": dst,
        "ttl": ttl,
        "headers": [{"id": str(uuid.uuid4())}],  # id único para evitar duplicados
        "payload": payload
    }


# Flooding
def flooding(graph: Dict[str, Dict[str, float]], start: str, packet: Dict[str, Any]) -> None:
    seen: Set[str] = set()  # paquetes ya vistos
    _flood_recursive(graph, start, packet, seen, prev=None)

def _flood_recursive(graph: Dict[str, Dict[str, float]], node: str, packet: Dict[str, Any], seen: Set[str], prev: str = None):
    pkt_id = packet["headers"][0]["id"]

    # evitar duplicados
    if pkt_id in seen:
        return
    seen.add(pkt_id)

    # decrementar TTL
    if packet["ttl"] <= 0:
        print(f"[{node}] TTL agotado, descartando paquete {pkt_id}")
        return

    # imprimir si soy el destino
    if node == packet["to"]:
        print(f"[{node}] Recibí mensaje: {packet['payload']}")
        return

    # reenviar a los vecinos
    for neigh in graph[node]:
        if neigh == prev:
            continue  # no enviar al que me lo mandó
        new_packet = packet.copy()
        new_packet["ttl"] -= 1
        print(f"[{node}] reenviando a {neigh} (ttl={new_packet['ttl']})")
        _flood_recursive(graph, neigh, new_packet, seen, prev=node)


# Ejemplo de uso
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python flooding_rt.py <topo.json> <origen> <destino>")
        sys.exit(1)

    topo_path = sys.argv[1]
    src = sys.argv[2]
    dst = sys.argv[3]

    graph = load_topology(topo_path)
    packet = make_packet("flooding", "message", src, dst, ttl=5, payload="Hola desde flooding!")

    flooding(graph, src, packet)
