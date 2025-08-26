import redis

# Conectar a Redis en localhost (puerto 6379)
r = redis.Redis(host='127.0.0.1', port=6379)

# Establecer un valor en Redis
r.set("mensaje", "¡Hola desde Redis!")

# Recuperar el valor
msg = r.get("mensaje")
print(f"Mensaje desde Redis: {msg.decode('utf-8')}")
