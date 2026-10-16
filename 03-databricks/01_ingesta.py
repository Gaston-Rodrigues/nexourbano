# Databricks notebook source

# ===== PARÁMETROS: cambiá solo esto para re-ejecutar con otra ciudad o fechas =====
CIUDAD = "Buenos Aires"
ZONA_HORARIA = "America/Argentina/Buenos_Aires"
FECHA_DESDE = "2026-03-01"
FECHA_HASTA = "2026-05-30"
RUTA_VIAJES = "/Volumes/workspace/nexourbano/nexo/viajes.csv"
TABLA_SILVER = "workspace.nexourbano.silver_clima_viajes"
HASHTAG_SOCIAL = "scooter"
TABLA_CLIMA = "workspace.nexourbano.silver_clima_horario"
TABLA_SOCIAL = "workspace.nexourbano.silver_social_menciones"

# COMMAND ----------

# 1. Leer el CSV de viajes (mismo millón de viajes que perfilamos en M1)
import pandas as pd

print(f"Ciudad: {CIUDAD} | Período: {FECHA_DESDE} a {FECHA_HASTA}")
viajes = pd.read_csv(RUTA_VIAJES)

# 2. Forma del dataset y nulos por columna
print("Filas y columnas:", viajes.shape)
print("\nNulos por columna:")
print(viajes.isnull().sum())

# 3. Primeras filas
display(viajes.head())

# COMMAND ----------

# 1. Pasar la fecha de inicio a hora de Buenos Aires (en el archivo está en UTC)
viajes["ts_start"] = pd.to_datetime(viajes["ts_start"])
viajes["hora_local"] = viajes["ts_start"].dt.tz_convert(ZONA_HORARIA).dt.hour

# 2. Métrica 1: viajes por hora del día (las 3 horas con más viajes)
por_hora = viajes.groupby("hora_local").size().sort_values(ascending=False)
print("1. Horas con más viajes:")
print(por_hora.head(3))

# 3. Métricas 2 y 3: duración mediana (p50) y p95, en minutos
p50 = viajes["duration_s"].quantile(0.50) / 60
p95 = viajes["duration_s"].quantile(0.95) / 60
print(f"\n2. Duración p50: {p50:.1f} minutos")
print(f"3. Duración p95: {p95:.1f} minutos")

# 4. Métrica 4: las 5 estaciones desde donde más viajes salen
print("\n4. Top 5 estaciones de origen:")
print(viajes["station_start"].value_counts().head(5))

# 5. Métrica 5: ingreso medio por viaje
print(f"\n5. Ingreso medio por viaje: {viajes['fare_ars'].mean():.2f} ARS")

# COMMAND ----------

# 1. Elegir las 3 estaciones con más viajes de salida
top3 = viajes["station_start"].value_counts().head(3).index

# 2. Quedarnos solo con los viajes que salen de esas 3 estaciones
viajes_top3 = viajes[viajes["station_start"].isin(top3)]

# 3. Ubicación de cada estación = promedio de lat/lon de sus viajes de salida
estaciones = viajes_top3.groupby("station_start")[["lat_start", "lon_start"]].mean().round(4)
estaciones = estaciones.reset_index()
display(estaciones)

# COMMAND ----------

# 1. Pedir a Open-Meteo el clima hora por hora de cada estación (historial, en UTC)
import json
import urllib.request

tablas = []   # acá juntamos el clima de cada estación
for i, est in estaciones.iterrows():
    url = ("https://archive-api.open-meteo.com/v1/archive"
           f"?latitude={est['lat_start']}&longitude={est['lon_start']}"
           f"&start_date={FECHA_DESDE}&end_date={FECHA_HASTA}"
           "&hourly=temperature_2m,precipitation,wind_speed_10m,weather_code")
    respuesta = json.loads(urllib.request.urlopen(url, timeout=60).read())
    tabla = pd.DataFrame(respuesta["hourly"])
    tabla["station_id"] = est["station_start"]    # de qué estación es
    tablas.append(tabla)

# 2. Juntar las tablas y ponerles los nombres del contrato (silver_clima.yaml)
clima = pd.concat(tablas)
clima = clima.rename(columns={"time": "ts_hora", "temperature_2m": "temp_c",
                              "precipitation": "precip_mm", "wind_speed_10m": "wind_kmh"})
clima["ts_hora"] = pd.to_datetime(clima["ts_hora"]).dt.tz_localize("UTC")

print("Filas y columnas del clima:", clima.shape)
display(clima.head())

# COMMAND ----------

# Reglas de calidad del contrato silver_clima.yaml

# C1: weather_code tiene que estar en la lista de códigos de clima válidos (tabla WMO)
codigos_validos = [0, 1, 2, 3, 45, 48, 51, 53, 55, 56, 57, 61, 63, 65, 66, 67,
                   71, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99]
c1_ok = clima["weather_code"].isin(codigos_validos)

# C2: la temperatura tiene que estar entre -10 y 50 grados
c2_ok = clima["temp_c"].between(-10, 50)

print(f"C1 rechazados (código de clima inválido): {(~c1_ok).sum()}")
print(f"C2 rechazados (temperatura fuera de rango): {(~c2_ok).sum()}")

# Nos quedamos solo con las filas que cumplen las dos reglas
clima_ok = clima[c1_ok & c2_ok]
print(f"Clima válido: {len(clima_ok)} de {len(clima)} filas")

# COMMAND ----------

# Feed social público: Mastodon, posts con un hashtag (no requiere API key)
import re

url = f"https://mastodon.social/api/v1/timelines/tag/{HASHTAG_SOCIAL}?limit=40"
pedido = urllib.request.Request(url, headers={"User-Agent": "nexourbano-tp"})
posts = json.loads(urllib.request.urlopen(pedido, timeout=30).read())

# Armar la tabla con las columnas del contrato silver_social.yaml
social = pd.DataFrame({
    "post_uri": [p["uri"] for p in posts],
    "created_at": [p["created_at"] for p in posts],
    "text": [re.sub("<[^>]+>", "", p["content"]) for p in posts],   # sacamos las etiquetas HTML
    "plataforma": "mastodon",
})

# Reglas de calidad: P1 post_uri único, P2 texto no vacío
social = social.drop_duplicates("post_uri")
social = social[social["text"].str.strip() != ""]

print(f"Posts válidos: {len(social)}")
print(f"Fechas: de {social['created_at'].min()} a {social['created_at'].max()}")
display(social.head())

# COMMAND ----------

# Reglas del contrato bronze_viajes.yaml

# La fecha de fin viene como texto: la pasamos a fecha
ts_fin = pd.to_datetime(viajes["ts_end"])

# R1: la duración tiene que estar entre 30 segundos y 4 horas (14400 s)
r1_ok = viajes["duration_s"].between(30, 14400)

# R2: la distancia tiene que ser mayor a 0
r2_ok = viajes["km"] > 0

# R3: el viaje tiene que terminar después de empezar
r3_ok = ts_fin > viajes["ts_start"]

# R4: el ride_id no puede estar repetido
r4_ok = viajes["ride_id"].duplicated() == False

# R5: rider_id, vehicle_id y station_start no pueden ser nulos
r5_ok = viajes["rider_id"].notnull() & viajes["vehicle_id"].notnull() & viajes["station_start"].notnull()

# Mostrar cuántos viajes rompe cada regla
print("R1 rechazados (duración):", (r1_ok == False).sum())
print("R2 rechazados (km <= 0):", (r2_ok == False).sum())
print("R3 rechazados (fin antes del inicio):", (r3_ok == False).sum())
print("R4 rechazados (ride_id repetido):", (r4_ok == False).sum())
print("R5 rechazados (nulos):", (r5_ok == False).sum())

# R6: velocidad media en km/h. Solo avisamos, NO rechazamos
velocidad = viajes["km"] / (viajes["duration_s"] / 3600)
print("R6 aviso (velocidad > 60 km/h):", (velocidad > 60).sum())

# Separar: los que cumplen TODAS las reglas van a Silver, el resto a cuarentena
todas_ok = r1_ok & r2_ok & r3_ok & r4_ok & r5_ok
silver_viajes = viajes[todas_ok]
cuarentena = viajes[todas_ok == False]

print("\nViajes en Bronze:", len(viajes))
print("Viajes en Silver:", len(silver_viajes))
print("Viajes en cuarentena:", len(cuarentena))
print("Silver + cuarentena = Bronze ?", len(silver_viajes) + len(cuarentena) == len(viajes))

# COMMAND ----------

# 1. Quedarnos con los viajes válidos que salen de las 3 estaciones con clima
viajes_3 = silver_viajes[silver_viajes["station_start"].isin(top3)].copy()

# 2. Crear la clave de la hora: 10:46 pasa a ser 10:00 (en UTC, igual que el clima)
viajes_3["ts_hora"] = viajes_3["ts_start"].dt.floor("h")

# 3. Ponerle a la estación el mismo nombre que tiene en la tabla de clima
viajes_3 = viajes_3.rename(columns={"station_start": "station_id"})

# 4. Cruzar (JOIN) viajes con clima por estación y hora
silver_clima_viajes = viajes_3.merge(clima_ok, on=["station_id", "ts_hora"], how="left")

# 5. Revisar el resultado
print("Filas y columnas:", silver_clima_viajes.shape)
print("Viajes sin clima:", silver_clima_viajes["weather_code"].isnull().sum())
display(silver_clima_viajes[["ride_id", "station_id", "ts_hora", "duration_s", "temp_c", "precip_mm", "weather_code"]].head())

# COMMAND ----------

# 1. Pasar la fecha de fin a fecha (venía como texto)
silver_clima_viajes["ts_end"] = pd.to_datetime(silver_clima_viajes["ts_end"])

# 2. Hora local de Buenos Aires, fecha y hora del día
silver_clima_viajes["ts_local"] = silver_clima_viajes["ts_start"].dt.tz_convert(ZONA_HORARIA)
silver_clima_viajes["fecha"] = silver_clima_viajes["ts_local"].dt.date
silver_clima_viajes["hora"] = silver_clima_viajes["ts_local"].dt.hour

# 3. Duración en minutos
silver_clima_viajes["duracion_min"] = silver_clima_viajes["duration_s"] / 60

# 4. Clima adverso: código de clima 51 o más (llovizna, lluvia, chubascos, tormenta)
silver_clima_viajes["clima_adverso"] = silver_clima_viajes["weather_code"] >= 51

# 5. Volver a llamar station_start a la estación, como dice el contrato
silver_clima_viajes = silver_clima_viajes.rename(columns={"station_id": "station_start"})

# 6. Quedarnos solo con las columnas que definimos para Silver
columnas = ["ride_id", "ts_start", "ts_end", "ts_local", "fecha", "hora",
            "duration_s", "duracion_min", "rider_id", "vehicle_id", "station_start",
            "km", "fare_ars", "temp_c", "precip_mm", "weather_code", "clima_adverso"]
silver_clima_viajes = silver_clima_viajes[columnas]

# 7. Revisar
print("Filas y columnas:", silver_clima_viajes.shape)
porcentaje = 100 * silver_clima_viajes["clima_adverso"].mean()
print(f"Viajes con clima adverso: {porcentaje:.1f} %")
display(silver_clima_viajes.head())

# COMMAND ----------

# 1. Pasar la tabla de pandas a Spark (el motor de Databricks)
tabla_spark = spark.createDataFrame(silver_clima_viajes)

# 2. Guardarla como tabla Delta en el esquema nexourbano
#    "overwrite" reemplaza la tabla si ya existe: así el notebook se puede re-ejecutar
tabla_spark.write.mode("overwrite").saveAsTable(TABLA_SILVER)

# 3. Comprobar que quedó guardada: contar filas y ver el formato
print("Filas guardadas en", TABLA_SILVER, ":", spark.table(TABLA_SILVER).count())
display(spark.sql(f"DESCRIBE DETAIL {TABLA_SILVER}").select("format", "numFiles", "sizeInBytes"))

# COMMAND ----------

# 1. Guardar el clima válido (silver_clima.yaml)
spark.createDataFrame(clima_ok).write.mode("overwrite").saveAsTable(TABLA_CLIMA)

# 2. Guardar los posts de Mastodon (silver_social.yaml)
#    created_at venía como texto: lo pasamos a fecha antes de guardar
social["created_at"] = pd.to_datetime(social["created_at"])
spark.createDataFrame(social).write.mode("overwrite").saveAsTable(TABLA_SOCIAL)

# 3. Comprobar cuántas filas tiene cada tabla
print("Clima:", spark.table(TABLA_CLIMA).count(), "filas")
print("Social:", spark.table(TABLA_SOCIAL).count(), "filas")

# COMMAND ----------

# MAGIC %md
# MAGIC