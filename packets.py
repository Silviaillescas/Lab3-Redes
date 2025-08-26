# packets.py
"""
Definición y utilidades de paquetes para la red basada en Redis (y sockets).
Formato estándar:
{
  "type": "message|hello|hello_ack|lsp|info|echo|...",
  "from": "<id_canal_origen>",   # p.ej. "sec10.grupo1.a"
  "to":   "<id_canal_destino>",  # p.ej. "sec10.grupo1.b" o "broadcast" si aplica
  "hops": 8,                     # entero, decrementa en cada reenvío
  "headers": [{"id": "<uuid4>"}, ...],  # se usa id para evitar duplicados
  "payload": "<string u objeto serializable>"
}
"""

from __future__ import annotations
import uuid
from typing import Dict, Any, Optional, Iterable

ALLOWED_TYPES: Iterable[str] = {
    "message",
    "hello",
    "hello_ack",
    "lsp",
    "info",
    "echo",
}

def make_packet(
    pkt_type: str,
    src: str,
    dst: str,
    hops: int = 8,
    payload: Any = "",
    headers: Optional[list[dict]] = None,
) -> Dict[str, Any]:
    """
    Crea un paquete con el formato estándar y un UUID nuevo en headers.
    - pkt_type: debe estar en ALLOWED_TYPES (puedes desactivar la validación si lo prefieres)
    - src, dst: IDs de canal Redis o nodos (si usas sockets); para Redis deben ser los canales reales
    - hops: entero positivo; se decrementa en cada forward
    - payload: string u objeto serializable a JSON
    - headers: lista opcional; se agrega siempre un {"id": uuid4}
    """
    if pkt_type not in ALLOWED_TYPES:
        # No detiene la ejecución, pero avisa en logs
        print(f"[packets.make_packet] Advertencia: tipo '{pkt_type}' no en ALLOWED_TYPES")

    if not isinstance(hops, int) or hops < 0:
        raise ValueError("hops debe ser un entero >= 0")

    base_headers = headers[:] if headers else []
    base_headers.append({"id": str(uuid.uuid4())})

    return {
        "type": pkt_type,
        "from": str(src),
        "to": str(dst),
        "hops": int(hops),
        "headers": base_headers,
        "payload": payload,
    }

def get_packet_id(packet: Dict[str, Any]) -> Optional[str]:
    """
    Extrae el primer headers[i]['id'] si existe, para control de duplicados.
    """
    try:
        hs = packet.get("headers", [])
        if isinstance(hs, list) and hs:
            pid = hs[0].get("id")
            return str(pid) if pid is not None else None
    except Exception:
        pass
    return None

def dec_hops(packet: Dict[str, Any]) -> int:
    """
    Decrementa 'hops' con seguridad y devuelve el nuevo valor.
    Si no existe hops, lo asume como 0.
    """
    h = int(packet.get("hops", 0))
    h -= 1
    packet["hops"] = h
    return h

def is_deliver_to_me(packet: Dict[str, Any], my_channel: str) -> bool:
    """
    ¿Este paquete es para mi canal o es broadcast?
    """
    dst = str(packet.get("to", ""))
    return dst == my_channel or dst.lower() == "broadcast"

def validate_packet(packet: Dict[str, Any]) -> bool:
    """
    Validación ligera del paquete. Devuelve True si pasa validaciones básicas.
    Útil antes de hacer forward o procesar payloads.
    """
    try:
        if not isinstance(packet, dict):
            return False

        # Campos obligatorios 
        for k in ("type", "from", "to", "hops", "headers", "payload"):
            if k not in packet:
                return False

        # Tipos esperados
        if not isinstance(packet["type"], str):
            return False
        if not isinstance(packet["from"], str):
            return False
        if not isinstance(packet["to"], str):
            return False
        if not isinstance(packet["hops"], int):
            return False
        if not isinstance(packet["headers"], list):
            return False
        # payload puede ser cualquier cosa serializable a JSON; no lo forzamos aquí

        # headers[0].id debe existir para control de duplicados
        pid = get_packet_id(packet)
        if not pid:
            return False

        return True
    except Exception:
        return False

def normalize_packet(packet: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza ciertos campos para evitar inconsistencias (p.ej. strings en hops).
    No hace validación estricta, solo intenta 'sanear' lo obvio.
    """
    p = dict(packet)  # copia superficial
    try:
        p["type"] = str(p.get("type", "message"))
        p["from"] = str(p.get("from", ""))
        p["to"] = str(p.get("to", ""))
        p["hops"] = int(p.get("hops", 0))
        if not isinstance(p.get("headers", []), list):
            p["headers"] = []
        # Garantizar un id si no existe
        if get_packet_id(p) is None:
            p["headers"] = p.get("headers", []) + [{"id": str(uuid.uuid4())}]
        return p
    except Exception:
        # Si algo sale mal, retorna el original sin romper el flujo
        return packet
