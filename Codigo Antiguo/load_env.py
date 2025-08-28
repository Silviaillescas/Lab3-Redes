# load_env.py - Carga variables de entorno desde .env
import os
from pathlib import Path

def load_env():
    """Carga variables de entorno desde archivo .env"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print(f"✅ Variables cargadas desde {env_file}")
    else:
        print(f"⚠️  Archivo .env no encontrado en {env_file}")

if __name__ == "__main__":
    load_env()
