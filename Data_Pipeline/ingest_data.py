import os
import glob
from pathlib import Path

import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

#verificar coonexion a la base de datos MongoDB Atlas
if not MONGO_URI:
    print("Error: La variable MONGO_URI no se encontró en tu archivo .env.")
    print("Asegúrate de que el archivo .env está en la misma carpeta y contiene la URI.")
    exit() # Detiene el script si no hay URI

print("Intentando conectar a MongoDB Atlas...")

# 2. Intenta conectar y enviar un "ping"
client = None # Inicializa el cliente como None
try:
    # Crea un cliente para conectar a la base de datos
    client = MongoClient(MONGO_URI)

    # El comando 'ping' fuerza una conexión y comprueba la autenticación.
    # Si esto falla, saltará directamente al bloque 'except'.
    client.admin.command('ping')
    
    # Si el ping tiene éxito, imprime este mensaje
    print("¡Éxito! La conexión a MongoDB Atlas se estableció correctamente.")

except Exception as e:
    # Si algo falla durante la conexión, imprime el error específico
    print(f"La conexión falló. Error: {e}")
    
finally:
    # 3. Cierra la conexión si se estableció
    if client:
        client.close()
        print("Conexión cerrada.")

print("\nVerificación de conexión finalizada.")