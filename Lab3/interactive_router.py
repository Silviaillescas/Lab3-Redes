#!/usr/bin/env python3
"""
Router Interactivo para Laboratorio 3 - Algoritmos de Enrutamiento
Permite enviar mensajes manualmente usando los algoritmos implementados.

Configuración de Redis (variables de entorno):
    export REDIS_HOST="lab3.redesuvg.cloud"
    export REDIS_PORT="6379" 
    export REDIS_PWD="UVGRedis2025"

Uso:
    python interactive_router.py <topo.json> <Nodo> [algoritmo]
    
Algoritmos disponibles: flooding, distance_vector, link_state
"""

import sys
import json
import time
import threading
from typing import Dict, Any

# Importar los routers implementados
from router_flooding_redis import FloodingRouterRedis
from dijkstra_rt import load_topology
from id_map import NODE_TO_CHANNEL, get_channel
from packets import make_packet


class InteractiveRouter:
    def __init__(self, node_id: str, graph: Dict[str, Dict[str, float]], algorithm: str = "flooding"):
        self.node_id = node_id
        self.algorithm = algorithm
        
        # Inicializar el router según el algoritmo seleccionado
        if algorithm == "flooding":
            self.router = FloodingRouterRedis(node_id, graph)
        else:
            raise ValueError(f"Algoritmo '{algorithm}' no implementado aún")
        
        print(f"\n🚀 Router {node_id} iniciado con algoritmo: {algorithm}")
        print(f"📡 Canal: {NODE_TO_CHANNEL[node_id]}")
        print(f"🔗 Vecinos: {list(graph.get(node_id, {}).keys())}")
        print("\n" + "="*50)

    def start(self):
        """Inicia el router y la interfaz interactiva"""
        # Iniciar el router en un hilo separado
        router_thread = threading.Thread(target=self.router.start, daemon=True)
        router_thread.start()
        
        # Esperar un momento para que se establezca la conexión
        time.sleep(2)
        
        # Mostrar menú de ayuda
        self.show_help()
        
        # Iniciar interfaz interactiva
        self.interactive_loop()

    def show_help(self):
        """Muestra el menú de ayuda"""
        print("\n📋 COMANDOS DISPONIBLES:")
        print("  send <destino> <mensaje>     - Enviar mensaje a un nodo")
        print("  broadcast <mensaje>          - Enviar mensaje a todos (*)")
        print("  hello <destino>              - Enviar paquete HELLO/PING")
        print("  info <destino>               - Enviar paquete de información")
        print("  echo <destino> <mensaje>     - Enviar paquete ECHO")
        print("  status                       - Mostrar estado del nodo")
        print("  nodes                        - Mostrar nodos disponibles")
        print("  help                         - Mostrar esta ayuda")
        print("  quit                         - Salir del programa")
        print("\n💡 Ejemplos:")
        print("  send B Hola desde A!")
        print("  broadcast Mensaje para todos")
        print("  hello C")
        print("="*50)

    def interactive_loop(self):
        """Loop principal de la interfaz interactiva"""
        try:
            while True:
                try:
                    # Prompt personalizado
                    cmd = input(f"\n[{self.node_id}]> ").strip()
                    
                    if not cmd:
                        continue
                        
                    # Procesar comando
                    self.process_command(cmd)
                        
                except KeyboardInterrupt:
                    print("\n\n👋 Saliendo...")
                    break
                except EOFError:
                    print("\n\n👋 Saliendo...")
                    break
                    
        finally:
            try:
                self.router.transport.stop()
            except:
                pass

    def process_command(self, cmd: str):
        """Procesa un comando ingresado por el usuario"""
        parts = cmd.split()
        if not parts:
            return
            
        command = parts[0].lower()
        
        if command == "send":
            if len(parts) < 3:
                print("❌ Uso: send <destino> <mensaje>")
                return
            dest = parts[1]
            message = " ".join(parts[2:])
            self.send_message(dest, message, "message")
            
        elif command == "broadcast":
            if len(parts) < 2:
                print("❌ Uso: broadcast <mensaje>")
                return
            message = " ".join(parts[1:])
            self.send_message("*", message, "message")
            
        elif command == "hello":
            if len(parts) < 2:
                print("❌ Uso: hello <destino>")
                return
            dest = parts[1]
            self.send_message(dest, f"HELLO from {self.node_id}", "hello")
            
        elif command == "info":
            if len(parts) < 2:
                print("❌ Uso: info <destino>")
                return
            dest = parts[1]
            info_data = {
                "node": self.node_id,
                "algorithm": self.algorithm,
                "neighbors": list(self.router.neighbors),
                "timestamp": time.time()
            }
            self.send_message(dest, json.dumps(info_data), "info")
            
        elif command == "echo":
            if len(parts) < 3:
                print("❌ Uso: echo <destino> <mensaje>")
                return
            dest = parts[1]
            message = " ".join(parts[2:])
            self.send_message(dest, message, "echo")
            
        elif command == "status":
            self.show_status()
            
        elif command == "nodes":
            self.show_nodes()
            
        elif command == "help":
            self.show_help()
            
        elif command in ["quit", "exit", "q"]:
            raise KeyboardInterrupt
            
        else:
            print(f"❌ Comando desconocido: {command}")
            print("💡 Escribe 'help' para ver los comandos disponibles")

    def send_message(self, dest: str, payload: str, msg_type: str = "message", hops: int = 8):
        """Envía un mensaje usando el router"""
        try:
            if dest == "*":
                print(f"📡 Enviando {msg_type} broadcast: {payload}")
            else:
                print(f"📤 Enviando {msg_type} a {dest}: {payload}")
            
            # Usar el método send del router (que maneja flooding automáticamente)
            if hasattr(self.router, 'send'):
                self.router.send(dest, payload, hops)
            else:
                print("❌ Método send no disponible en este router")
                
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")

    def show_status(self):
        """Muestra el estado actual del nodo"""
        print(f"\n📊 ESTADO DEL NODO {self.node_id}")
        print(f"  Algoritmo: {self.algorithm}")
        print(f"  Canal: {NODE_TO_CHANNEL[self.node_id]}")
        print(f"  Vecinos: {self.router.neighbors}")
        print(f"  Paquetes vistos: {len(self.router.seen)}")

    def show_nodes(self):
        """Muestra todos los nodos disponibles"""
        print("\n🌐 NODOS DISPONIBLES:")
        for node_id, channel in NODE_TO_CHANNEL.items():
            status = "🟢 (YO)" if node_id == self.node_id else "⚪"
            print(f"  {status} {node_id} -> {channel}")


def main():
    if len(sys.argv) < 3:
        print("Uso: python interactive_router.py <topo.json> <Nodo> [algoritmo]")
        print("Algoritmos disponibles: flooding (default)")
        print("\nEjemplo: python interactive_router.py topo.json A")
        print("         python interactive_router.py topo.json A flooding")
        sys.exit(1)

    topo_path = sys.argv[1]
    node = sys.argv[2]
    algorithm = sys.argv[3] if len(sys.argv) > 3 else "flooding"

    try:
        graph = load_topology(topo_path)
    except Exception as e:
        print(f"❌ Error cargando topología '{topo_path}': {e}")
        sys.exit(2)

    if node not in graph:
        print(f"❌ Nodo '{node}' no existe en la topología")
        print(f"Nodos disponibles: {list(graph.keys())}")
        sys.exit(3)

    import os
    if not os.getenv("REDIS_HOST"):
        print("⚠️  CONFIGURACIÓN REQUERIDA:")
        print("export REDIS_HOST='lab3.redesuvg.cloud'")
        print("export REDIS_PORT='6379'")
        print("export REDIS_PWD='UVGRedis2025'")
        print("\nEjecuta estos comandos antes de iniciar el router.")
        sys.exit(1)

    # Crear y iniciar router interactivo
    interactive_router = InteractiveRouter(node, graph, algorithm)
    interactive_router.start()


if __name__ == "__main__":
    main()
