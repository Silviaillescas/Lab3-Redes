import subprocess
import sys
import time
import json
from typing import Dict, List

def load_topology(path: str) -> Dict[str, List[str]]:
    """Load topology configuration"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("config", {})

def start_lsr_network(topology_file: str):
    """Start all LSR nodes based on topology"""
    
    topology = load_topology(topology_file)
    processes = []
    
    print("Starting LSR network...")
    print(f"Topology: {topology}")
    
    # Start each node
    for node_id in topology.keys():
        print(f"Starting LSR node {node_id}...")
        
        cmd = [sys.executable, "link_state_routing.py", topology_file, node_id]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            processes.append((node_id, process))
            time.sleep(1)  # Small delay between starting nodes
            
        except Exception as e:
            print(f"Error starting node {node_id}: {e}")
    
    print(f"\nStarted {len(processes)} LSR nodes")
    print("Waiting for network to stabilize...")
    time.sleep(5)
    
    print("\nLSR Network is running!")
    print("You can now:")
    print("1. Use lsr_client.py to send messages between nodes")
    print("2. Press Ctrl+C to stop all nodes")
    
    try:
        # Monitor processes
        while True:
            for node_id, process in processes:
                if process.poll() is not None:
                    print(f"Node {node_id} has stopped")
                    processes.remove((node_id, process))
            
            if not processes:
                print("All nodes have stopped")
                break
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping all LSR nodes...")
        for node_id, process in processes:
            process.terminate()
            print(f"Stopped node {node_id}")
        
        # Wait for processes to terminate
        for node_id, process in processes:
            process.wait()
        
        print("All nodes stopped.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_lsr_network.py <topology_file>")
        print("Example: python run_lsr_network.py topo.json")
        sys.exit(1)
    
    topology_file = sys.argv[1]
    start_lsr_network(topology_file)

if __name__ == "__main__":
    main()
