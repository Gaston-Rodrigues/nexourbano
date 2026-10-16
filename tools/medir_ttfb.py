# medir_ttfb.py - M2: mide el time-to-first-byte de MinIO (para el ADR 001)
# Pide el archivo viajes.csv 10 veces y mide cuánto tarda en llegar el primer byte.
# Uso:  py tools\medir_ttfb.py
import os
import statistics
import time
from minio import Minio

BUCKET = "bronze"
ARCHIVO = "viajes/2026/10/15/viajes.csv"
SALIDA = "evidence/azure/04_ttfb_minio.txt"

# 1. Leer usuario y clave del archivo .env (así no quedan escritos en el código)
claves = {}
for linea in open(".env", encoding="utf-8"):
    if "=" in linea and not linea.startswith("#"):
        nombre, valor = linea.strip().split("=", 1)
        claves[nombre] = valor

# 2. Conectarse a MinIO
cliente = Minio("localhost:9000", access_key=claves["MINIO_ROOT_USER"],
                secret_key=claves["MINIO_ROOT_PASSWORD"], secure=False)

# 3. Pedir el archivo 10 veces y medir hasta el primer byte
tiempos = []
for i in range(10):
    inicio = time.perf_counter()
    respuesta = cliente.get_object(BUCKET, ARCHIVO)
    respuesta.read(1)                                   # leemos solo 1 byte
    milisegundos = (time.perf_counter() - inicio) * 1000
    respuesta.close()
    respuesta.release_conn()
    tiempos.append(milisegundos)
    print(f"Intento {i + 1}: {milisegundos:.1f} ms")

# 4. Resumen
resumen = (f"TTFB MinIO local, 10 intentos: mediana {statistics.median(tiempos):.1f} ms, "
           f"mínimo {min(tiempos):.1f} ms, máximo {max(tiempos):.1f} ms")
print("\n" + resumen)

# 5. Guardar como evidencia
os.makedirs("evidence/azure", exist_ok=True)
with open(SALIDA, "w", encoding="utf-8") as f:
    f.write(resumen)
print(f"Guardado en {SALIDA}")