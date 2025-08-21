#!/usr/bin/env python3
"""
Test script for Link State Routing implementation
"""

import subprocess
import time
import sys
import os

def run_test():
    """Run comprehensive LSR tests"""
    
    print("=== Link State Routing Test Suite ===\n")
    
    # Test 1: Start network
    print("Test 1: Starting LSR network...")
    network_process = None
    
    try:
        # Start the network in background
        network_process = subprocess.Popen([
            sys.executable, "run_lsr_network.py", "topo.json"
        ])
        
        print("Network starting... waiting 10 seconds for stabilization")
        time.sleep(10)
        
        # Test 2: Send messages between nodes
        print("\nTest 2: Sending test messages...")
        
        test_messages = [
            ("A", "D", "Hello from A to D via LSR"),
            ("B", "C", "Message from B to C"),
            ("D", "A", "Reply from D to A"),
            ("C", "B", "Response from C to B")
        ]
        
        for source, dest, message in test_messages:
            print(f"Sending: {source} -> {dest}: '{message}'")
            
            try:
                result = subprocess.run([
                    sys.executable, "lsr_client.py", source, dest, message
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    print(f"  ✓ Message sent successfully")
                else:
                    print(f"  ✗ Error: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print(f"  ✗ Timeout sending message")
            except Exception as e:
                print(f"  ✗ Exception: {e}")
            
            time.sleep(2)
        
        print("\nTest 3: Network convergence test...")
        print("Waiting 5 seconds for routing tables to converge...")
        time.sleep(5)
        
        # Send final test messages
        final_tests = [
            ("A", "C", "Final test A->C"),
            ("D", "B", "Final test D->B")
        ]
        
        for source, dest, message in final_tests:
            print(f"Final test: {source} -> {dest}")
            try:
                subprocess.run([
                    sys.executable, "lsr_client.py", source, dest, message
                ], timeout=3)
                print(f"  ✓ Sent")
            except:
                print(f"  ✗ Failed")
        
        print("\n=== LSR Test Complete ===")
        print("Check the network output for routing table updates and message delivery")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test error: {e}")
    finally:
        if network_process:
            print("\nStopping network...")
            network_process.terminate()
            network_process.wait()
            print("Network stopped")

if __name__ == "__main__":
    # Change to parent directory to run tests
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    os.chdir(parent_dir)
    
    run_test()
