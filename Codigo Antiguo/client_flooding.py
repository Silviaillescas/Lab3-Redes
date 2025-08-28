import socket
import json
import uuid

# Para correr el programa:
# python client_flooding.py


HOST = "127.0.0.1"
BASE_PORT = 1235  # mismo esquema que en router_flooding

# Crear paquete JSON
def make_packet(src: str, dst: str, ttl: int, payload: str) -> dict:
    return {
        "proto": "flooding",
        "type": "message",
        "from": src,
        "to": dst,
        "ttl": ttl,
        "headers": [{"id": str(uuid.uuid4())}],  # identificador único
        "payload": payload
    }

def send_packet(src: str, dst: str, ttl: int, payload: str):
    port = BASE_PORT + (ord(src) - ord("A"))  # puerto del router origen
    packet = make_packet(src, dst, ttl, payload)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, port))
            s.send(json.dumps(packet).encode("utf-8"))
            print(f"[Cliente] Paquete enviado desde {src} hacia {dst} (ttl={ttl})")
    except ConnectionRefusedError:
        print(f"[Cliente] No pude conectar con el router {src} en {HOST}:{port}")

if __name__ == "__main__":
    # Ejemplo: mandar mensaje de A a D
    origen = "A"
    destino = "D"
    ttl = 5
    mensaje = "Hola desde cliente externo!"

    send_packet(origen, destino, ttl, mensaje)
