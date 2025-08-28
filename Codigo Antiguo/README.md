# Proyecto de Enrutamiento y Forwarding con Dijkstra, Flooding y Link State Routing
Silvia Illescas, Alex Cuxe y Michelle Mejia

Este proyecto implementa un sistema de **enrutamiento** y **forwarding** utilizando tres algoritmos principales de enrutamiento: **Dijkstra**, **Flooding** y **Link State Routing**. El sistema emplea **sockets** y **hilos** para gestionar la **comunicación entre routers** y el **reenviar de paquetes** de manera eficiente.

## Informe 
https://uvggt-my.sharepoint.com/:w:/g/personal/mej22596_uvg_edu_gt/ESmpCkpNvwVIn65AXcImPR8B6nwJgvSydDT6mOmTlbl0dQ?e=djfn7E

## Descripción

Este proyecto tiene como objetivo implementar tres algoritmos de enrutamiento: **Dijkstra**, **Flooding** y **Link State Routing**, para calcular las rutas más cortas y reenviar paquetes dentro de una red de **routers**. El sistema utiliza **sockets** para la comunicación entre routers y **hilos** para manejar múltiples conexiones de manera concurrente.

### Algoritmos Implementados:
1. **Dijkstra**: Algoritmo de enrutamiento basado en la búsqueda de la ruta más corta.
2. **Flooding**: Algoritmo de enrutamiento que propaga paquetes a todos los nodos vecinos.
3. **Link State Routing**: Algoritmo que permite a los routers compartir el estado de sus enlaces y calcular las rutas usando el algoritmo de Dijkstra sobre una visión global de la red.

## Estructura del Proyecto

1. **`router.py`**: Implementa los tres algoritmos de enrutamiento (Dijkstra, Flooding y Link State Routing) y maneja las conexiones de otros routers.
2. **`client.py`**: Simula un cliente (router) que envía un destino y recibe la respuesta del router con el siguiente salto (next hop).
3. **`topo.json`**: Archivo de entrada que contiene la topología de la red, donde se especifican los nodos y las conexiones con sus respectivos costos.

## Cómo Funciona

1. El **servidor** (router) lee el archivo de topología (`topo.json`) que contiene las conexiones entre los nodos.
2. El servidor puede ejecutar cualquiera de los tres algoritmos de enrutamiento:
   - **Dijkstra**: Calcula las rutas más cortas desde el nodo origen a todos los destinos.
   - **Flooding**: Propaga los paquetes a todos los nodos vecinos sin necesidad de calcular rutas.
   - **Link State Routing**: Cada nodo envía su **estado de enlace** (información sobre sus vecinos y los costos) a todos los demás nodos. Luego, cada nodo calcula la mejor ruta a todos los destinos utilizando el algoritmo de Dijkstra basado en la **información global**.
3. Cuando un cliente (router) envía una solicitud con un destino específico, el servidor calcula la ruta más corta (o propaga el paquete, dependiendo del algoritmo seleccionado) y responde con el siguiente salto (next hop), la ruta completa y el costo total.
4. El cliente puede usar esta información para reenviar el paquete al siguiente salto en la red.

## Requisitos

- Python 3.x
- Librerías estándar de Python (sin necesidad de librerías adicionales).

## Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/Silviaillescas/Lab3-Redes.git
``

## Uso

### 1. Ejecutar el servidor

El servidor (`router.py`) debe ser ejecutado primero. Asegúrate de tener el archivo `topo.json` con la topología de la red y ejecuta el servidor con el nodo origen de tu elección y el algoritmo de enrutamiento que desees utilizar.

Ejemplo para ejecutar con **Dijkstra**:

```bash
python router.py topo.json A Dijkstra
```

Ejemplo para ejecutar con **Flooding**:

```bash
python router.py topo.json A Flooding
```

Ejemplo para ejecutar con **Link State Routing**:

```bash
python router.py topo.json A LinkStateRouting
```

Esto iniciará el servidor en **127.0.0.1** en el puerto **12345**. El servidor comenzará a escuchar por conexiones entrantes y calculará las rutas usando el algoritmo seleccionado.

### 2. Ejecutar el cliente

Después de ejecutar el servidor, puedes iniciar el cliente (`client.py`) para enviar solicitudes de enrutamiento. El cliente enviará el destino del paquete y recibirá la ruta y el siguiente salto (next hop).

Ejemplo:

```bash
python client.py
```

Esto enviará una solicitud para reenviar un paquete a un destino (por ejemplo, **D**), y el servidor responderá con la ruta y el siguiente salto.

## Ejemplo de Respuesta

**Servidor**:

```bash
Paquete recibido para el destino: D
Ruta calculada por Dijkstra desde A a D: ['A', 'B', 'D']
Respuesta del router: Paquete reenviado a B, Ruta: A → B → D, Costo total: 2
```

**Cliente**:

```bash
Respuesta del router: Paquete reenviado a B, Ruta: A → B → D, Costo total: 2
```

## Funcionamiento en Paralelo

El servidor maneja múltiples conexiones de manera asíncrona utilizando **hilos**. Cada vez que se recibe una conexión (por ejemplo, de un cliente), se crea un nuevo hilo que maneja esa conexión sin bloquear el resto de las operaciones.
