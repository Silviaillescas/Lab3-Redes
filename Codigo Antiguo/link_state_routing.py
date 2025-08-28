import json
import socket
import threading
import time
import uuid
import sys
from typing import Dict, List, Set, Any, Optional, Tuple
from dijkstra_rt import dijkstra, routing_table_for, load_topology
from flooding_rt import make_packet

class LinkStateRouter:
    def __init__(self, node_id: str, topology_file: str, port: int):
        self.node_id = node_id
        self.port = port
        self.topology_file = topology_file

        # Load initial topology to know neighbors
        self.graph = load_topology(topology_file)
        self.neighbors = list(self.graph.get(node_id, {}).keys())

        # Link State Database - stores LSPs from all nodes
        self.lsdb: Dict[str, Dict[str, Any]] = {}

        # Routing table
        self.routing_table: List[Dict[str, Any]] = []

        # Sequence number for our LSPs
        self.sequence_number = 0

        # Set to track seen LSPs (to avoid loops)
        self.seen_lsps: Set[str] = set()

        # Socket for communication
        self.socket = None

        # Threads
        self.forwarding_thread = None
        self.routing_thread = None

        # Running flag
        self.running = False

        print(f"[{self.node_id}] Initialized LSR node with neighbors: {self.neighbors}")

    def start(self):
        """Start the LSR node with forwarding and routing processes"""
        self.running = True

        # Start socket server for forwarding
        self.forwarding_thread = threading.Thread(target=self.forwarding_process)
        self.forwarding_thread.daemon = True
        self.forwarding_thread.start()

        # Start routing process
        self.routing_thread = threading.Thread(target=self.routing_process)
        self.routing_thread.daemon = True
        self.routing_thread.start()

        print(f"[{self.node_id}] LSR node started on port {self.port}")

    def forwarding_process(self):
        """Handle incoming packets - forwarding process"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.socket.bind(('127.0.0.1', self.port))
            self.socket.listen(5)
            print(f"[{self.node_id}] Forwarding process listening on port {self.port}")

            while self.running:
                try:
                    client_socket, addr = self.socket.accept()
                    threading.Thread(target=self.handle_packet, args=(client_socket,)).start()
                except Exception as e:
                    if self.running:
                        print(f"[{self.node_id}] Error in forwarding process: {e}")
        except Exception as e:
            print(f"[{self.node_id}] Failed to start forwarding process: {e}")

    def handle_packet(self, client_socket: socket.socket):
        """Handle individual incoming packets"""
        try:
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                return

            packet = json.loads(data)
            packet_type = packet.get("type", "")

            print(f"[{self.node_id}] Received packet type: {packet_type} from {packet.get('from', 'unknown')}")

            if packet_type == "hello":
                self.handle_hello_packet(packet, client_socket)
            elif packet_type == "lsp":
                self.handle_lsp_packet(packet)
            elif packet_type == "message":
                self.handle_data_packet(packet)
            else:
                print(f"[{self.node_id}] Unknown packet type: {packet_type}")

        except Exception as e:
            print(f"[{self.node_id}] Error handling packet: {e}")
        finally:
            client_socket.close()

    def handle_hello_packet(self, packet: Dict[str, Any], client_socket: socket.socket):
        """Handle HELLO packets for neighbor discovery"""
        sender = packet.get("from", "")

        # Send HELLO response
        response = make_packet("lsr", "hello_ack", self.node_id, sender, 1, "Hello ACK")
        try:
            client_socket.send(json.dumps(response).encode('utf-8'))
            print(f"[{self.node_id}] Sent HELLO ACK to {sender}")
        except Exception as e:
            print(f"[{self.node_id}] Error sending HELLO ACK: {e}")

    def handle_lsp_packet(self, packet: Dict[str, Any]):
        """Handle Link State Packet (LSP)"""
        lsp_id = packet["headers"][0].get("lsp_id", "")
        originator = packet.get("originator", "")

        # Check if we've already seen this LSP
        if lsp_id in self.seen_lsps:
            print(f"[{self.node_id}] Already seen LSP {lsp_id}, ignoring")
            return

        self.seen_lsps.add(lsp_id)

        # Store LSP in database
        self.lsdb[originator] = packet
        print(f"[{self.node_id}] Stored LSP from {originator}")

        # Flood LSP to neighbors (except sender)
        sender = packet.get("from", "")
        self.flood_lsp(packet, exclude=sender)

        # Trigger routing table recalculation
        self.calculate_routing_table()

    def handle_data_packet(self, packet: Dict[str, Any]):
        """Handle data packets that need forwarding"""
        destination = packet.get("to", "")

        # Check if packet is for us
        if destination == self.node_id:
            print(f"[{self.node_id}] Received message: {packet.get('payload', '')}")
            return

        # Forward packet using routing table
        next_hop = self.get_next_hop(destination)
        if next_hop:
            self.forward_packet_to(packet, next_hop)
        else:
            print(f"[{self.node_id}] No route to {destination}")

    def routing_process(self):
        """Routing process - generates and sends LSPs periodically"""
        time.sleep(2)  # Wait for forwarding process to start

        while self.running:
            try:
                # Send HELLO to discover neighbors
                self.send_hello_to_neighbors()
                time.sleep(1)

                # Generate and flood our LSP
                self.generate_and_flood_lsp()

                # Wait before next iteration
                time.sleep(10)

            except Exception as e:
                print(f"[{self.node_id}] Error in routing process: {e}")
                time.sleep(5)

    def send_hello_to_neighbors(self):
        """Send HELLO packets to all neighbors"""
        for neighbor in self.neighbors:
            hello_packet = make_packet("lsr", "hello", self.node_id, neighbor, 1, "Hello")
            self.send_packet_to_node(hello_packet, neighbor)

    def generate_and_flood_lsp(self):
        """Generate our Link State Packet and flood it"""
        self.sequence_number += 1
        lsp_id = f"{self.node_id}_{self.sequence_number}_{int(time.time())}"

        # Create LSP with our link state information
        lsp = {
            "proto": "lsr",
            "type": "lsp",
            "from": self.node_id,
            "to": "broadcast",
            "ttl": 10,
            "headers": [{"lsp_id": lsp_id}],
            "originator": self.node_id,
            "sequence": self.sequence_number,
            "neighbors": self.graph.get(self.node_id, {}),
            "timestamp": int(time.time()),
            "payload": f"LSP from {self.node_id}"
        }

        # Store our own LSP
        self.lsdb[self.node_id] = lsp

        # Flood to all neighbors
        self.flood_lsp(lsp)

        print(f"[{self.node_id}] Generated and flooded LSP {lsp_id}")

    def flood_lsp(self, lsp: Dict[str, Any], exclude: str = None):
        """Flood LSP to all neighbors except excluded node"""
        for neighbor in self.neighbors:
            if neighbor != exclude:
                # Create copy with decremented TTL
                lsp_copy = lsp.copy()
                lsp_copy["ttl"] -= 1
                lsp_copy["from"] = self.node_id

                if lsp_copy["ttl"] > 0:
                    self.send_packet_to_node(lsp_copy, neighbor)

    def calculate_routing_table(self):
        """Calculate routing table using Dijkstra on the topology derived from LSPs"""
        # Build complete topology from LSDB
        complete_graph = {}

        for node, lsp in self.lsdb.items():
            neighbors = lsp.get("neighbors", {})
            complete_graph[node] = neighbors

        # Ensure all nodes exist in graph
        all_nodes = set(complete_graph.keys())
        for node in all_nodes:
            complete_graph.setdefault(node, {})

        print(f"[{self.node_id}] Complete topology from LSDB: {complete_graph}")

        # Calculate routing table using Dijkstra
        if self.node_id in complete_graph:
            self.routing_table = routing_table_for(complete_graph, self.node_id)
            print(f"[{self.node_id}] Updated routing table:")
            for entry in self.routing_table:
                print(f"  -> {entry['destino']}: next_hop={entry['next_hop']}, cost={entry['costo']}")

    def get_next_hop(self, destination: str) -> Optional[str]:
        """Get next hop for a destination from routing table"""
        for entry in self.routing_table:
            if entry["destino"] == destination:
                return entry["next_hop"]
        return None

    def send_packet_to_node(self, packet: Dict[str, Any], target_node: str):
        """Send packet to a specific node"""
        # In a real implementation, you'd need a mapping of node_id to (host, port)
        # For this simulation, we'll use a simple port mapping
        port_mapping = {
            'A': 8001, 'B': 8002, 'C': 8003, 'D': 8004,
            'E': 8005, 'F': 8006, 'G': 8007, 'H': 8008
        }

        target_port = port_mapping.get(target_node)
        if not target_port:
            print(f"[{self.node_id}] No port mapping for {target_node}")
            return

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect(('127.0.0.1', target_port))
            sock.send(json.dumps(packet).encode('utf-8'))
            sock.close()

        except Exception as e:
            print(f"[{self.node_id}] Failed to send packet to {target_node}: {e}")

    def forward_packet_to(self, packet: Dict[str, Any], next_hop: str):
        """Forward a data packet to the next hop"""
        packet["from"] = self.node_id
        packet["ttl"] -= 1

        if packet["ttl"] > 0:
            self.send_packet_to_node(packet, next_hop)
            print(f"[{self.node_id}] Forwarded packet to {next_hop}")
        else:
            print(f"[{self.node_id}] Packet TTL expired, dropping")

    def send_message(self, destination: str, message: str):
        """Send a message to a destination"""
        packet = make_packet("lsr", "message", self.node_id, destination, 10, message)

        next_hop = self.get_next_hop(destination)
        if next_hop:
            self.send_packet_to_node(packet, next_hop)
            print(f"[{self.node_id}] Sent message to {destination} via {next_hop}")
        else:
            print(f"[{self.node_id}] No route to {destination}")

    def stop(self):
        """Stop the LSR node"""
        self.running = False
        if self.socket:
            self.socket.close()

def main():
    if len(sys.argv) < 3:
        print("Usage: python link_state_routing.py <topology_file> <node_id> [port]")
        sys.exit(1)

    topology_file = sys.argv[1]
    node_id = sys.argv[2]
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 8000

    # Port mapping for different nodes
    port_mapping = {
        'A': 8001, 'B': 8002, 'C': 8003, 'D': 8004,
        'E': 8005, 'F': 8006, 'G': 8007, 'H': 8008
    }

    if node_id in port_mapping:
        port = port_mapping[node_id]

    router = LinkStateRouter(node_id, topology_file, port)
    router.start()

    print(f"LSR Router {node_id} started. Press Enter to send test message or 'quit' to exit.")

    try:
        while True:
            user_input = input().strip()
            if user_input.lower() == 'quit':
                break
            elif user_input.startswith('send '):
                parts = user_input.split(' ', 2)
                if len(parts) >= 3:
                    dest = parts[1]
                    msg = parts[2]
                    router.send_message(dest, msg)
                else:
                    print("Usage: send <destination> <message>")
            elif user_input == '':
                # Send test message
                test_destinations = ['A', 'B', 'C', 'D']
                for dest in test_destinations:
                    if dest != node_id:
                        router.send_message(dest, f"Test message from {node_id}")
                        break
    except KeyboardInterrupt:
        pass
    finally:
        router.stop()
        print(f"LSR Router {node_id} stopped.")

if __name__ == "__main__":
    main()
