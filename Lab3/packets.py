

# packets.py
from __future__ import annotations
import uuid
import time
from typing import Any, Dict, List, Optional

BROADCAST = "*"

def _now_ms() -> int:
    return int(time.time() * 1000)

def make_packet(p_type: str,
                from_channel: str,
                to_channel: str,
                hops: int = 8,
                headers: Optional[List[Dict[str, Any]]] = None,
                payload: Any = "") -> Dict[str, Any]:
    if headers is None:
        headers = []
    if not headers or "id" not in headers[0]:
        headers = [{"id": str(uuid.uuid4()), "ts": _now_ms()}] + headers
    return {
        "type": p_type,
        "from": from_channel,
        "to": to_channel,
        "hops": int(hops),
        "headers": headers,
        "payload": payload
    }

def normalize_packet(pkt: Dict[str, Any]) -> Dict[str, Any]:
    return pkt

def validate_packet(pkt: Dict[str, Any]) -> bool:
    try:
        if not isinstance(pkt, dict): return False
        for k in ("type", "from", "to", "hops", "headers"):
            if k not in pkt: return False
        if not isinstance(pkt["type"], str): return False
        if not isinstance(pkt["from"], str): return False
        if not isinstance(pkt["to"], str): return False
        if not isinstance(pkt["hops"], int): return False
        if not isinstance(pkt["headers"], list): return False
        return True
    except Exception:
        return False

def get_packet_id(pkt: Dict[str, Any]) -> str:
    try:
        return pkt.get("headers", [{}])[0].get("id", "")
    except Exception:
        return ""

def dec_hops(pkt: Dict[str, Any]) -> int:
    try:
        pkt["hops"] = int(pkt.get("hops", 0)) - 1
    except Exception:
        pkt["hops"] = -1
    return pkt["hops"]

def is_deliver_to_me(pkt: Dict[str, Any], my_channel: str) -> bool:
    to_ch = pkt.get("to", "")
    return to_ch == my_channel or to_ch == BROADCAST
