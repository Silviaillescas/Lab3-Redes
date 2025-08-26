import redis

# Conectar a Redis en localhost (puerto 6379)
r = redis.Redis(host='127.0.0.1', port=6379)

# Realizar un test de conexión
print("Conectado:", r.ping())  # Si la conexión es exitosa, debe imprimir True

