#!/usr/bin/env python3
"""Chequeo rápido del entorno: archivos generados, .env y puertos de cada servicio.
    py scripts/verificar_entorno.py
"""
import socket
from pathlib import Path

ARCHIVOS = ["data/viajes.csv", "data/viajes_muestra.csv", "data/riders.csv", "data/lecturas_sensores.csv",
            "data/productos.json", "data/ventas.csv", "data/grafo.json", "data/texto_ops.txt",
            "data/app.log", "data/mysql/crm_riders.sql"]
PUERTOS = {"MinIO API": 9000, "MinIO consola": 9001, "MySQL": 3307, "MongoDB": 27018,
           "Cassandra": 9042, "Neo4j bolt": 7687, "HDFS namenode UI": 9870, "HDFS rpc": 8020,
           "YARN": 8088, "HiveServer2": 10000, "HBase UI": 16010, "Spark UI": 4040}

print("== Archivos (py tools/generar_datos.py --seed 131 --n-viajes 1000000) ==")
for f in ARCHIVOS:
    p = Path(f)
    print(f"  {'OK ' if p.exists() else 'FALTA'} {f}" + (f"  ({p.stat().st_size/1e6:.1f} MB)" if p.exists() else ""))
print("\n== .env ==\n ", "OK" if Path(".env").exists() else "FALTA: cp .env.example .env")
print("\n== Puertos (servicios levantados) ==")
for nombre, puerto in PUERTOS.items():
    with socket.socket() as s:
        s.settimeout(0.4)
        abierto = s.connect_ex(("127.0.0.1", puerto)) == 0
    print(f"  {'ARRIBA' if abierto else '------'} {nombre:18s} :{puerto}")
