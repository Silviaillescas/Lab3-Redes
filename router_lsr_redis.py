# router_lsr_redis.py
"""
Router de Link State Routing (LSR) usando Redis Pub/Sub como red.
- Descubre vecinos con HELLO
- Inunda LSPs a través de la red
- Construye LSDB, calcula tabla de ruteo con Dijkstra
- Reenvía paquetes de datos

Requisitos:
    pip install redis
Variables de entorno:
    export REDIS_HOST="... "
    export REDIS_PORT="6379"
    export REDIS_PWD="... "
Ejecución (ejemplo):
    python router_lsr_redis.py topo.json A
"""

from __future__ import annotations
import json
import sys
import time
from typing import Dict, Set, Any, List
from collections import deque

# Utilidades locales
from redis_transport import RedisTransport
from id_map import NODE_TO_CHANNEL, get_channel
from packets import make_packet, validate_packet, normalize_packet, get_packet_id, dec_hops, is_deliver_to_me

# Reutilizamos el loader de topología (puedes cambiarlo por el tuyo si prefieres)
from dijkstra_rt import load_topology


class LinkStateRouterRedis:
    def __init__(self, node_id: str, graph: Dict[str, Dict[str, float]]):
        if node_id not in NODE_TO_CHANNEL:
            raise ValueError(f"Nodo '{node_id}' no está en NODE_TO_CHANNEL")

        self.node_id = node_id
        self.channel_local: str = NODE_TO_CHANNEL[node_id]

        # vecinos lógicos (nodos directos del grafo)
        self.neighbors: List[str] = list(graph.get(node_id, {}).keys())

        # bases para LSR: LSDB, secuencia de LSPs y tabla de ruteo
        self.lsdb: Dict[str, Dict[str, Any]] = {}
        self.sequence_number = 0
        self.seen_lsp_ids: Set[str] = set()
        self.routing_table: List[Dict[str, Any]] = []

        # transporte Redis (callback en _on_packet)
        self.transport = RedisTransport(self.channel_local, self._on_packet)

        print(f"[{self.node_id}] Iniciado. Canal={self.channel_local} Vecinos={self.neighbors}")

    def start(self) -> None:
        """Inicia el proceso de enrutamiento LSR con Redis."""
        self.transport.start()
        print(f"[{self.node_id}] Escuchando en Redis... (Ctrl+C para salir)")

    # ======== Recepción de paquetes ========

    def _on_packet(self, packet: Dict[str, Any]) -> None:
        # Normalizamos y validamos
        packet = normalize_packet(packet)
        if not validate_packet(packet):
            return  # ignorar malformados

        # Si es un mensaje HELLO
        if packet["type"] == "hello":
            self._handle_hello(packet)

        # Si es un LSP (Link State Packet)
        elif packet["type"] == "lsp":
            self._handle_lsp(packet)

        # Si es un paquete de datos (por ejemplo, mensaje a reenviar)
        elif packet["type"] == "message":
            self._handle_data_packet(packet)

    def _handle_hello(self, packet: Dict[str, Any]) -> None:
        """Procesa un paquete 'hello' para descubrir vecinos"""
        sender = packet.get("from", "")
        if sender not in self.neighbors:
            self.neighbors.append(sender)
            print(f"[{self.node_id}] Nuevo vecino descubierto: {sender}")

        # Responder al vecino con un ACK
        ack_packet = make_packet("hello_ack", self.channel_local, sender, hops=1, payload="Hello ACK")
        self.transport.publish(sender, ack_packet)

    def _handle_lsp(self, packet: Dict[str, Any]) -> None:
        """Procesa un LSP y actualiza la LSDB"""
        lsp_id = get_packet_id(packet)
        if not lsp_id or lsp_id in self.seen_lsp_ids:
            return  # evitar duplicados

        self.seen_lsp_ids.add(lsp_id)
        originator = packet.get("originator", "")

        # Almacenamos el LSP
        self.lsdb[originator] = packet
        print(f"[{self.node_id}] LSP recibido de {originator}")

        # Inundar LSP a los vecinos (excepto el que lo mandó)
        self._flood_lsp(packet, exclude=packet["from"])

        # Recalcular la tabla de ruteo
        self._calculate_routing_table()

    def _handle_data_packet(self, packet: Dict[str, Any]) -> None:
        """Reenvía un paquete de datos a su siguiente salto"""
        destination = packet.get("to", "")
        if destination == self.node_id:
            print(f"[{self.node_id}] Mensaje recibido: {packet.get('payload')}")
            return  # Si es para mí, simplemente lo recibo

        next_hop = self._get_next_hop(destination)
        if next_hop:
            self._forward_packet(packet, next_hop)
        else:
            print(f"[{self.node_id}] No hay ruta para {destination}")

    # ======== Forwarding y LSP ========

    def _flood_lsp(self, packet: Dict[str, Any], exclude: str = None) -> None:
        """Inunda el LSP a todos los vecinos excepto el que lo envió"""
        for neigh in self.neighbors:
            if neigh == exclude:
                continue
            self.transport.publish(get_channel(neigh), packet)
            print(f"[{self.node_id}] LSP reenviado a {neigh}")

    def _forward_packet(self, packet: Dict[str, Any], next_hop: str) -> None:
        """Reenvía un paquete a su siguiente salto usando la tabla de ruteo"""
        packet["hops"] -= 1  # Decrementa hops antes de reenviar
        next_hop_channel = get_channel(next_hop)
        self.transport.publish(next_hop_channel, packet)
        print(f"[{self.node_id}] Paquete reenviado a {next_hop} via {next_hop_channel}")

    # ======== Cálculo de tabla de ruteo ========

    def _calculate_routing_table(self) -> None:
        """Calcula la tabla de ruteo usando la LSDB"""
        # Construir el grafo completo desde la LSDB
        complete_graph = {}
        for node, lsp in self.lsdb.items():
            complete_graph[node] = lsp.get("neighbors", {})

        # Calcular la tabla de ruteo con Dijkstra
        print(f"[{self.node_id}] Calculando tabla de ruteo...")
        from dijkstra_rt import routing_table_for
        self.routing_table = routing_table_for(complete_graph, self.node_id)

        # Mostrar la tabla de ruteo calculada
        print(f"[{self.node_id}] Tabla de ruteo calculada:")
        for entry in self.routing_table:
            print(f"  -> {entry['destino']}: next_hop={entry['next_hop']}, cost={entry['costo']}")

    def _get_next_hop(self, destination: str) -> str:
        """Obtiene el siguiente salto de la tabla de ruteo"""
        if not hasattr(self, 'routing_table') or not self.routing_table:
            print(f"[{self.node_id}] Tabla de ruteo vacía, no se puede enrutar a {destination}")
            return ""
            
        for entry in self.routing_table:
            if entry["destino"] == destination:
                return entry["next_hop"]
        return ""

    # ======== Enviar mensajes ========

    def send(self, dst_node: str, payload: str, hops: int = 8) -> None:
        """Envía un mensaje a través de LSR"""
        pkt = make_packet("message", self.node_id, dst_node, hops=hops, payload=payload)
        
        # Si el destino es un vecino directo, enviar directamente
        if dst_node in self.neighbors:
            dst_channel = get_channel(dst_node)
            self.transport.publish(dst_channel, pkt)
            print(f"[{self.node_id}] Mensaje enviado directamente a vecino {dst_node}")
        else:
            # Usar la tabla de ruteo para encontrar el siguiente salto
            next_hop = self._get_next_hop(dst_node)
            if next_hop:
                next_hop_channel = get_channel(next_hop)
                self.transport.publish(next_hop_channel, pkt)
                print(f"[{self.node_id}] Mensaje enviado a {dst_node} via {next_hop}")
            else:
                print(f"[{self.node_id}] No hay ruta para {dst_node}")


def main():
    if len(sys.argv) < 3:
        print("Uso: python router_lsr_redis.py <topo.json> <Nodo>")
        sys.exit(1)

    topo_path = sys.argv[1]
    node = sys.argv[2]

    try:
        graph = load_topology(topo_path)
    except Exception as e:
        print(f"Error cargando topología '{topo_path}': {e}")
        sys.exit(2)

    router = LinkStateRouterRedis(node, graph)

    try:
        router.start()

        # Enviar un mensaje de prueba 
        if node == "A":  # Si soy A, envío mensaje de prueba
            time.sleep(1.5)
            router.send("D", "Hola desde A con LSR+Redis!", hops=6)

        # Mantener vivo el proceso
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nSaliendo...")
    finally:
        try:
            router.transport.stop()
        except Exception:
            pass


if __name__ == "__main__":
    main()
