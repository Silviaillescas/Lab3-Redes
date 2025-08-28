#!/usr/bin/env python3
"""
Script to test Redis messaging between nodes
"""
import time
import sys
from lsr_client_redis import send_message_via_redis

def test_messaging():
    """Test various message scenarios"""
    
    print("🧪 Testing Redis LSR Messaging...")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        ("A", "D", "Hello from A to D via LSR!"),
        ("B", "C", "Message from B to C"),
        ("D", "A", "Reply from D back to A"),
        ("C", "B", "Testing reverse path C->B")
    ]
    
    for i, (source, dest, message) in enumerate(test_cases, 1):
        print(f"\n📨 Test {i}: {source} → {dest}")
        send_message_via_redis(source, dest, message)
        time.sleep(2)  # Wait between messages
    
    print("\n✅ All test messages sent!")
    print("Check your router terminals to see if messages were received.")

if __name__ == "__main__":
    test_messaging()
