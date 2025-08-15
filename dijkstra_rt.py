import json
import sys
import heapq
from typing import Dict, List, Tuple, Optional, Any

# Lectura de topología (formato del anexo del lab)
def load_topology(path: str) -> Dict[str, Dict[str, float]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cfg = data.get("config", {})
    graph: Dict[str, Dict[str, float]] = {}
    for u, neigh in cfg.items():
        if isinstance(neigh, dict):
            # ya trae pesos
            graph[u] = {v: float(w) for v, w in neigh.items()}
        else:
            # lista simple: asignar peso 1
            graph[u] = {v: 1.0 for v in neigh}
    # Asegurar nodos aislados aparezcan
    for u in list(cfg.keys()):
        graph.setdefault(u, {})
    return graph

# Dijkstra clásico con heap
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

# Reconstrucción de ruta y cálculo de next-hop
def rebuild_path(prev: Dict[str, Optional[str]], source: str, target: str) -> List[str]:
    path: List[str] = []
    cur: Optional[str] = target
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    if not path or path[0] != source:
        return []  # sin ruta
    return path

def next_hop_from_path(path: List[str]) -> Optional[str]:
    if len(path) >= 2:
        return path[1]
    return None

# Tabla de enrutamiento para un origen
def routing_table_for(graph: Dict[str, Dict[str, float]], source: str) -> List[Dict[str, Any]]:
    dist, prev = dijkstra(graph, source)
    rows = []
    for dst in sorted(graph.keys()):
        if dst == source:
            continue
        path = rebuild_path(prev, source, dst)
        nh = next_hop_from_path(path)
        cost = dist[dst] if path else float("inf")
        rows.append({
            "destino": dst,
            "costo": None if cost == float("inf") else cost,
            "next_hop": nh,
            "ruta": "→".join(path) if path else "∅"
        })
    return rows

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python dijkstra_rt.py <topo.json> <origen>")
        sys.exit(1)
    topo_path = sys.argv[1]
    source = sys.argv[2]
    graph = load_topology(topo_path)
    if source not in graph:
        print(f"El origen '{source}' no existe en la topología.")
        sys.exit(2)
    table = routing_table_for(graph, source)
    # Imprimir tabla
    print(f"Tabla de enrutamiento (origen = {source})")
    print(f"{'Destino':<10} {'Costo':<10} {'NextHop':<10} Ruta")
    for r in table:
        c = "∞" if r['costo'] is None else f"{r['costo']:.2f}"
        print(f"{r['destino']:<10} {c:<10} {str(r['next_hop']):<10} {r['ruta']}")
