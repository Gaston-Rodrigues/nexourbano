# descargar_dataset_abierto.py - M1: baja un mes de Citi Bike NYC (dataset abierto real)
# Fuente: https://s3.amazonaws.com/tripdata/index.html
# Uso:  py tools\descargar_dataset_abierto.py
import os
import urllib.request

MES = "202609"                                                   # año y mes (septiembre 2026)
URL = f"https://s3.amazonaws.com/tripdata/{MES}-citibike-tripdata.zip"
DESTINO = f"data/open/citibike_{MES}.zip"

# 1. Crear la carpeta donde se guarda (si no existe)
os.makedirs("data/open", exist_ok=True)

# 2. Descargar el zip (pesa casi 1 GB, tarda unos minutos)
print(f"Bajando {URL}")
print("Esto tarda unos minutos, esperá...")
urllib.request.urlretrieve(URL, DESTINO)

# 3. Mostrar el tamaño del archivo bajado
mb = os.path.getsize(DESTINO) / 1_000_000
print(f"Listo: {DESTINO} ({mb:,.0f} MB)")