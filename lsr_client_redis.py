import json
import sys
import redis
from packets import make_packet
from id_map import NODE_TO_CHANNEL

import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

REDIS_HOST = os.getenv("REDIS_HOST", "lab3.redesuvg.cloud")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PWD = os.getenv("REDIS_PWD", "UVGRedis2025")

def send_message_via_redis(source_node: str, dest_node: str, message: str):
    """Send a message through the Redis LSR network"""
    
    # Validate nodes exist in mapping
    if source_node not in NODE_TO_CHANNEL:
        print(f"Unknown source node: {source_node}")
        return
    
    if dest_node not in NODE_TO_CHANNEL:
        print(f"Unknown destination node: {dest_node}")
        return
    
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PWD, decode_responses=True)
    
    try:
        # Create message packet
        packet = make_packet(
            pkt_type="message",
            src=source_node,
            dst=dest_node,
            payload=message,
            hops=10
        )
        
        # Get source channel
        source_channel = NODE_TO_CHANNEL[source_node]
        
        r.publish(source_channel, json.dumps(packet))
        
        print(f"✅ Message sent from {source_node} to {dest_node}: '{message}'")
        print(f"📡 Published to channel: {source_channel}")
        
    except Exception as e:
        print(f"❌ Error sending message: {e}")
    finally:
        r.close()

def main():
    if len(sys.argv) < 4:
        print("Usage: python lsr_client_redis.py <source_node> <dest_node> <message>")
        print("Example: python lsr_client_redis.py A D 'Hello from A to D'")
        print(f"Available nodes: {list(NODE_TO_CHANNEL.keys())}")
        sys.exit(1)
    
    source = sys.argv[1].upper()
    destination = sys.argv[2].upper()
    message = ' '.join(sys.argv[3:])
    
    send_message_via_redis(source, destination, message)

if __name__ == "__main__":
    main()
