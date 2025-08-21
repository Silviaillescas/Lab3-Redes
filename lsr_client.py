import socket
import json
import sys
from link_state_routing import LinkStateRouter
from flooding_rt import make_packet

def send_message_via_lsr(source_node: str, dest_node: str, message: str):
    """Send a message through the LSR network"""
    
    # Port mapping for nodes
    port_mapping = {
        'A': 8001, 'B': 8002, 'C': 8003, 'D': 8004,
        'E': 8005, 'F': 8006, 'G': 8007, 'H': 8008
    }
    
    source_port = port_mapping.get(source_node)
    if not source_port:
        print(f"Unknown source node: {source_node}")
        return
    
    # Create message packet
    packet = make_packet("lsr", "message", source_node, dest_node, 10, message)
    
    try:
        # Connect to source node
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', source_port))
        
        # Send packet
        sock.send(json.dumps(packet).encode('utf-8'))
        sock.close()
        
        print(f"Message sent from {source_node} to {dest_node}: {message}")
        
    except Exception as e:
        print(f"Error sending message: {e}")

def main():
    if len(sys.argv) < 4:
        print("Usage: python lsr_client.py <source_node> <dest_node> <message>")
        print("Example: python lsr_client.py A D 'Hello from A to D'")
        sys.exit(1)
    
    source = sys.argv[1]
    destination = sys.argv[2]
    message = ' '.join(sys.argv[3:])
    
    send_message_via_lsr(source, destination, message)

if __name__ == "__main__":
    main()
