# id_map.py
"""
Este archivo mapea los nodos lógicos de tu red a los canales Redis reales.
Modifica este archivo según tu grupo y sección.

Ejemplo: topología cuadrada A-B-D-C del topo.json.
"""

# Aquí mapeamos los nodos lógicos de la red a los canales Redis reales
NODE_TO_CHANNEL = {
    "A": "sec10.grupo1.a",   # reemplazar con nuestro usuario real
    "B": "sec10.grupo1.b",     # idem
    "C": "sec10.grupo1.c",   # idem
    "D": "sec10.grupo1.d",   # idem
}

# Función auxiliar para validar nodos
def get_channel(node: str) -> str:
    """Devuelve el canal Redis correspondiente a un nodo lógico"""
    if node not in NODE_TO_CHANNEL:
        raise ValueError(f"Nodo desconocido: {node}")
    return NODE_TO_CHANNEL[node]
