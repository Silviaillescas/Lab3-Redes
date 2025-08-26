# redis_transport.py
# Adaptador simple de transporte vía Redis Pub/Sub.
# Usa variables de entorno para credenciales y NO expone secretos en el repo.

import os
import json
import threading
from typing import Callable, Dict, Any, Optional

try:
    import redis  # pip install redis
except ImportError as e:
    raise RuntimeError("Falta la librería 'redis'. Instala con: pip install redis") from e


def _env(name: str, default: Optional[str] = None) -> str:
    val = os.getenv(name, default)
    if val is None:
        raise RuntimeError(f"Variable de entorno requerida no definida: {name}")
    return val


REDIS_HOST = _env("REDIS_HOST", "")
REDIS_PORT = int(_env("REDIS_PORT", ""))
REDIS_PWD  = os.getenv("REDIS_PWD", "") 


class RedisTransport:
    """
    Adaptador de transporte vía Redis Pub/Sub.
    - channel_local: canal propio (ID único del nodo) p.ej. "sec10.grupo1.alice"
    - on_message: callback(packet_dict) para manejar cada paquete entrante
    """

    def __init__(self, channel_local: str, on_message: Callable[[Dict[str, Any]], None]):
        self.channel_local = channel_local
        self.on_message = on_message

        # Conexión principal (publicaciones) y una pubsub (suscripción)
        self._r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PWD, decode_responses=False)
        # Nota: decode_responses=False -> recibimos bytes y decodificamos manualmente

        self._pubsub = self._r.pubsub()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Comienza a escuchar el canal local en un hilo."""
        self._pubsub.subscribe(self.channel_local)
        self._thread = threading.Thread(target=self._listen_loop, name=f"RedisSub-{self.channel_local}", daemon=True)
        self._thread.start()

    def _listen_loop(self) -> None:
        for msg in self._pubsub.listen():
            if self._stop.is_set():
                break
            if msg.get("type") != "message":
                continue
            try:
                raw = msg["data"]
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8", errors="ignore")
                packet = json.loads(raw)
            except Exception:
                # Mensaje malformado: lo ignoramos
                continue
            try:
                self.on_message(packet)
            except Exception:
                # Evitar que un error en el callback tumbe el hilo
                pass

    def publish(self, channel: str, packet: Dict[str, Any]) -> None:
        """Publica un paquete JSON al canal indicado."""
        try:
            self._r.publish(channel, json.dumps(packet))
        except Exception as e:
            # Podrías loggear o reintentar
            print(f"[RedisTransport] Error publicando a {channel}: {e}")

    def stop(self) -> None:
        """Detiene la suscripción y cierra recursos."""
        self._stop.set()
        try:
            self._pubsub.unsubscribe(self.channel_local)
        except Exception:
            pass
        try:
            self._pubsub.close()
        except Exception:
            pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
