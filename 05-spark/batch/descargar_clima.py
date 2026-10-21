# Descarga el clima horario de Open-Meteo para las 3 estaciones con más viajes.
# Repite lo que hicimos en M3 (01_ingesta.py), pero guarda un CSV para usarlo en Spark.
import csv
import json
import urllib.request

RUTA_VIAJES = "/opt/nexo/data/viajes.csv"
RUTA_SALIDA = "/opt/nexo/data/clima_horario.csv"
FECHA_DESDE = "2026-03-01"
FECHA_HASTA = "2026-05-30"

# 1. Recorrer los viajes: contar salidas y sumar lat/lon por estación
cantidad = {}
suma_lat = {}
suma_lon = {}
with open(RUTA_VIAJES, newline="") as f:
    for fila in csv.DictReader(f):
        est = fila["station_start"]
        if est == "" or fila["lat_start"] == "" or fila["lon_start"] == "":
            continue
        cantidad[est] = cantidad.get(est, 0) + 1
        suma_lat[est] = suma_lat.get(est, 0) + float(fila["lat_start"])
        suma_lon[est] = suma_lon.get(est, 0) + float(fila["lon_start"])

# 2. Quedarnos con las 3 estaciones con más viajes de salida
top3 = sorted(cantidad, key=cantidad.get, reverse=True)[:3]

# 3. Códigos de clima válidos (regla C1 del contrato silver_clima.yaml)
codigos_validos = [0, 1, 2, 3, 45, 48, 51, 53, 55, 56, 57, 61, 63, 65, 66, 67,
                   71, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99]

filas_clima = []
total = 0
rechazados_c1 = 0
rechazados_c2 = 0

for est in top3:
    # Ubicación de la estación = promedio de lat/lon de sus viajes de salida
    lat = round(suma_lat[est] / cantidad[est], 4)
    lon = round(suma_lon[est] / cantidad[est], 4)
    print(est, "viajes:", cantidad[est], "lat:", lat, "lon:", lon)

    # 4. Pedir el clima hora por hora a Open-Meteo (historial, en UTC)
    url = ("https://archive-api.open-meteo.com/v1/archive"
           f"?latitude={lat}&longitude={lon}"
           f"&start_date={FECHA_DESDE}&end_date={FECHA_HASTA}"
           "&hourly=temperature_2m,precipitation,wind_speed_10m,weather_code")
    horario = json.loads(urllib.request.urlopen(url, timeout=60).read())["hourly"]

    for i in range(len(horario["time"])):
        total = total + 1
        temp = horario["temperature_2m"][i]
        codigo = horario["weather_code"][i]

        # C1: el weather_code tiene que estar en la lista WMO
        if codigo not in codigos_validos:
            rechazados_c1 = rechazados_c1 + 1
            continue
        # C2: la temperatura tiene que estar entre -10 y 50 grados
        if temp is None or temp < -10 or temp > 50:
            rechazados_c2 = rechazados_c2 + 1
            continue

        # La hora viene como 2026-03-01T00:00 (UTC): le agregamos segundos y zona
        ts_hora = horario["time"][i] + ":00+00:00"
        filas_clima.append([est, ts_hora, temp, horario["precipitation"][i],
                            horario["wind_speed_10m"][i], codigo])

# 5. Guardar el clima válido en un CSV
with open(RUTA_SALIDA, "w", newline="") as f:
    escritor = csv.writer(f)
    escritor.writerow(["station_id", "ts_hora", "temp_c", "precip_mm", "wind_kmh", "weather_code"])
    escritor.writerows(filas_clima)

print("Filas de clima recibidas:", total)
print("C1 rechazados (código inválido):", rechazados_c1)
print("C2 rechazados (temperatura fuera de rango):", rechazados_c2)
print("Clima válido guardado:", len(filas_clima)) 