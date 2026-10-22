# generador_stream.py - suelta un archivo JSON con eventos cada 2 segundos en data/stream/
import glob
import json
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone

CARPETA = "/opt/nexo/data/stream"
CANTIDAD_ARCHIVOS = int(sys.argv[1]) if len(sys.argv) > 1 else 170
EVENTOS_POR_ARCHIVO = 5

random.seed(131)
os.makedirs(CARPETA, exist_ok=True)
for viejo in glob.glob(CARPETA + "/eventos_*.json"):   # borrar solo los archivos de corridas anteriores del generador
    os.remove(viejo)

# Lista de tipos de evento: payment_fail y battery_low aparecen más para tener qué contar
TIPOS = ["ride_start", "ride_end", "unlock_ok", "ride_start", "ride_end", "unlock_ok",
         "payment_fail", "payment_fail", "battery_low", "battery_low"]


def ahora():
    return datetime.now(timezone.utc).replace(microsecond=0)


def crear_evento(momento, tipo=None, vehiculo=None):
    tipo = tipo or random.choice(TIPOS)
    if tipo == "battery_low":
        bateria = round(random.uniform(4, 17), 1)
    else:
        bateria = round(max(4.0, random.gauss(58, 20)), 1)
    return {"ts": momento.isoformat(), "event": tipo,
            "vehicle_id": vehiculo or "V%04d" % random.randint(0, 399),
            "rider_id": "R%04d" % random.randint(0, 119),
            "battery_pct": bateria}


for n in range(1, CANTIDAD_ARCHIVOS + 1):
    momento = ahora()
    eventos = [crear_evento(momento) for _ in range(EVENTOS_POR_ARCHIVO)]

    # Evento tardío DENTRO del watermark (40 s de atraso): Spark lo tiene que contar
    if n in (40, 80, 120):
        tarde = crear_evento(momento - timedelta(seconds=40), "payment_fail", "V9001")
        eventos.append(tarde)
        print(">> Archivo", n, ": evento tardío ACEPTADO (40 s de atraso):", json.dumps(tarde))

    # Evento tardío FUERA del watermark (240 s de atraso): Spark lo tiene que descartar
    if n == 150:
        tarde = crear_evento(momento - timedelta(seconds=240), "payment_fail", "V9002")
        eventos.append(tarde)
        print(">> Archivo", n, ": evento tardío DESCARTADO (240 s de atraso):", json.dumps(tarde))

    # Escribimos con nombre oculto (.nombre) y lo renombramos al final:
    # así Spark nunca lee un archivo a medio escribir
    nombre = "eventos_%04d.json" % n
    temporal = os.path.join(CARPETA, "." + nombre)
    with open(temporal, "w") as f:
        for e in eventos:
            f.write(json.dumps(e) + "\n")
    os.rename(temporal, os.path.join(CARPETA, nombre))
    time.sleep(2)

print(">> Generador terminado:", CANTIDAD_ARCHIVOS, "archivos")
