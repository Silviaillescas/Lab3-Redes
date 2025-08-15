import socket

HOST = '127.0.0.1'  # Dirección del router servidor
PORT = 12345         # Puerto de escucha del router

def send_packet(destination: str):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))  # Conectar al router
        client_socket.send(destination.encode('utf-8'))  # Enviar destino
        data = client_socket.recv(1024)  # Recibir respuesta
        print(f"Respuesta del router: {data.decode('utf-8')}")

if __name__ == "__main__":
    destino = 'D'  # Puedes probar con diferentes destinos
    send_packet(destino)
