# Lab3 - Algoritmos de Enrutamiento

## Descripción General

Este proyecto implementa y simula algoritmos de enrutamiento distribuido sobre una red Redis. Cada nodo de la red corresponde a un canal/usuario en el servidor Redis, permitiendo la comunicación entre múltiples instancias que simulan routers en una red real.

## Algoritmos Implementados

### 1. Flooding (Inundación)
El algoritmo de flooding envía cada paquete a todos los vecinos, excepto al que lo envió. Es simple pero ineficiente, ya que genera mucho tráfico redundante.

**Funcionamiento:**
- Cada nodo reenvía paquetes recibidos a todos sus vecinos
- Utiliza TTL (hops) para evitar loops infinitos
- Garantiza que el mensaje llegue al destino si existe una ruta

### 2. Link State Routing (LSR)
Algoritmo más sofisticado que construye un mapa completo de la topología de red y calcula rutas óptimas usando el algoritmo de Dijkstra.

**Fases del LSR:**
1. **Descubrimiento de Vecinos**: Envío periódico de paquetes HELLO
2. **Flooding de LSPs**: Distribución de Link State Packets con información de conectividad
3. **Construcción de LSDB**: Cada nodo mantiene una base de datos completa de la topología
4. **Cálculo de Rutas**: Uso de Dijkstra para encontrar caminos más cortos

## Arquitectura del Sistema

### Componentes Principales

**`packets.py`** - Define la estructura de paquetes JSON y operaciones básicas
- Creación, validación y manipulación de paquetes
- Soporte para diferentes tipos: message, hello, lsp, info

**`id_map.py`** - Mapeo entre identificadores de nodos y canales Redis
- Conversión entre IDs de nodos (A, B, C, D) y canales de usuario
- Formato: `sec{SECTION}.grupo{GROUP}.{username}`

**`dijkstra_rt.py`** - Implementación del algoritmo de Dijkstra
- Cálculo de rutas más cortas en grafos
- Construcción de tablas de enrutamiento

**`redis_transport.py`** - Abstracción de comunicación Redis
- Manejo de pub/sub para envío y recepción de mensajes
- Interfaz unificada para diferentes algoritmos

### Routers Implementados

**`router_flooding_redis.py`** - Router con algoritmo de flooding
- Reenvío simple a todos los vecinos
- Control de TTL para evitar loops

**`router_lsr_redis.py`** - Router con Link State Routing
- Descubrimiento automático de vecinos
- Construcción y mantenimiento de LSDB
- Cálculo dinámico de rutas óptimas

**`interactive_router.py`** - Interfaz interactiva unificada
- Soporte para múltiples algoritmos
- Comandos para envío manual de mensajes
- Visualización de estado del router

## Protocolo de Comunicación

Los nodos se comunican usando mensajes JSON estandarizados:

\`\`\`json
{
  "type": "message|hello|lsp|info",
  "from": "sec10.grupo1.usuario",
  "to": "sec10.grupo1.destino",
  "hops": 3,
  "headers": [{"id": "uuid", "timestamp": 1640995200}],
  "payload": "contenido del mensaje"
}
\`\`\`

### Tipos de Mensajes

- **message**: Mensajes de usuario final
- **hello/hello_ack**: Descubrimiento y mantenimiento de vecinos
- **lsp**: Link State Packets para distribución de topología
- **info**: Información de tablas de enrutamiento (Distance Vector)

## Topología de Red

La red se define mediante archivos JSON que especifican:
- **Topología**: Conexiones entre nodos (`topo.json`)
- **Nombres**: Mapeo de IDs a usuarios UVG (`names.json`)

Los nodos solo conocen sus vecinos directos inicialmente, y deben descubrir la topología completa mediante los algoritmos de enrutamiento.

## Características Técnicas

- **Comunicación Asíncrona**: Uso de Redis pub/sub para mensajería
- **Tolerancia a Fallos**: Manejo de nodos caídos y reconexiones
- **Escalabilidad**: Soporte para múltiples nodos simultáneos
- **Debugging**: Logs detallados y herramientas de diagnóstico
- **Modularidad**: Arquitectura extensible para nuevos algoritmos
</markdown>
