# job_gold.py - M8: Bronze -> Silver -> Gold con Spark
from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

ZONA = "America/Argentina/Buenos_Aires"
RUTA_VIAJES = "/opt/nexo/data/viajes.csv"
RUTA_CLIMA = "/opt/nexo/data/clima_horario.csv"
HDFS = "hdfs://namenode:8020"
RUTA_SILVER = HDFS + "/nexo/silver/viajes"

# Sesión de Spark: trabajamos en UTC y convertimos a hora local solo para analizar
spark = (SparkSession.builder.appName("job_gold")
         .config("spark.sql.session.timeZone", "UTC")
         .getOrCreate())
spark.sparkContext.setLogLevel("WARN")

# ========== 1. BRONZE: leer el CSV de viajes ==========
esquema = ("ride_id STRING, ts_start TIMESTAMP, ts_end TIMESTAMP, duration_s INT, "
           "rider_id STRING, vehicle_id STRING, station_start STRING, station_end STRING, "
           "barrio_start STRING, barrio_end STRING, lat_start DOUBLE, lon_start DOUBLE, "
           "lat_end DOUBLE, lon_end DOUBLE, km DOUBLE, fare_ars DOUBLE, clima_codigo INT")
bronze = spark.read.csv(RUTA_VIAJES, header=True, schema=esquema)

# Número de fila, para saber cuál ride_id repetido apareció primero
bronze = bronze.withColumn("id_fila", F.monotonically_increasing_id())
ventana = Window.partitionBy("ride_id").orderBy("id_fila")
bronze = bronze.withColumn("n_repeticion", F.row_number().over(ventana))
bronze = bronze.cache()   # lo vamos a usar varias veces: lo dejamos en memoria

n_bronze = bronze.count()
print(">> Viajes en Bronze:", n_bronze)

# ========== 2. REGLAS DE CALIDAD (las mismas de M3) ==========
r1 = F.col("duration_s").between(30, 14400)        # R1: duración entre 30 s y 4 horas
r2 = F.col("km") > 0                               # R2: distancia mayor a 0
r3 = F.col("ts_end") > F.col("ts_start")           # R3: termina después de empezar
r4 = F.col("n_repeticion") == 1                    # R4: ride_id sin repetir
r5 = (F.col("rider_id").isNotNull() & F.col("vehicle_id").isNotNull()
      & F.col("station_start").isNotNull())        # R5: sin nulos en claves

reglas = {"R1 duración": r1, "R2 km": r2, "R3 fin>inicio": r3,
          "R4 ride_id único": r4, "R5 nulos": r5}
for nombre, regla in reglas.items():
    rechazados = bronze.filter(~F.coalesce(regla, F.lit(False))).count()
    print(">> Rechazados", nombre, ":", rechazados)

# R6: velocidad mayor a 60 km/h. Solo avisa, no rechaza
velocidad = F.col("km") / (F.col("duration_s") / 3600)
print(">> Aviso R6 (velocidad > 60 km/h):", bronze.filter(velocidad > 60).count())

# Un viaje es válido si cumple TODAS las reglas (si alguna da nulo, cuenta como falla)
todas_ok = F.coalesce(r1 & r2 & r3 & r4 & r5, F.lit(False))
silver_base = bronze.filter(todas_ok)
cuarentena = bronze.filter(~todas_ok)

n_silver = silver_base.count()
n_cuarentena = cuarentena.count()
print(">> Viajes válidos (Silver):", n_silver)
print(">> Viajes en cuarentena:", n_cuarentena)
print(">> Silver + cuarentena = Bronze ?", n_silver + n_cuarentena == n_bronze)

# ========== 3. SILVER: hora local + join con clima ==========
clima = spark.read.csv(RUTA_CLIMA, header=True,
                       schema="station_id STRING, ts_hora TIMESTAMP, temp_c DOUBLE, "
                              "precip_mm DOUBLE, wind_kmh DOUBLE, weather_code INT")
clima = clima.withColumnRenamed("ts_hora", "clima_hora")

viajes = (silver_base
          .withColumn("ts_hora", F.date_trunc("hour", "ts_start"))       # 10:46 -> 10:00 (UTC)
          .withColumn("ts_local", F.from_utc_timestamp("ts_start", ZONA))  # hora de Buenos Aires
          .withColumn("fecha", F.to_date("ts_local"))
          .withColumn("hora", F.hour("ts_local"))
          .withColumn("duracion_min", F.col("duration_s") / 60))

# JOIN: cada viaje busca el clima de su estación y su hora (left: los demás quedan sin clima)
silver = viajes.join(
    clima,
    (viajes["station_start"] == clima["station_id"]) & (viajes["ts_hora"] == clima["clima_hora"]),
    "left")
silver = silver.withColumn("clima_adverso", F.col("weather_code") >= 51)

# Quedarnos con las columnas del contrato silver_viajes.yaml
silver = silver.select("ride_id", "ts_start", "ts_end", "ts_local", "fecha", "hora",
                       "duration_s", "duracion_min", "rider_id", "vehicle_id",
                       "station_start", "km", "fare_ars", "weather_code", "clima_adverso")

print(">> Viajes con clima:", silver.filter(F.col("weather_code").isNotNull()).count())

# Guardar Silver en HDFS: Parquet, una carpeta por fecha
(silver.repartition("fecha").write.mode("overwrite")
       .partitionBy("fecha").parquet(RUTA_SILVER))
print(">> Silver guardado en", RUTA_SILVER)

bronze.unpersist()   # Bronze ya no se necesita en memoria

# ========== 4. LEER SILVER DE HDFS Y UNIR CON RIDERS (M7) ==========
silver = spark.read.parquet(RUTA_SILVER)
print(">> Filas leídas de vuelta:", silver.count())

# riders: lo que Sqoop dejó en HDFS (CSV sin encabezado). Solo usamos rider_id y plan
riders = spark.read.csv(HDFS + "/nexo/bronze/riders_sqoop",
                        schema="rider_id STRING, nombre STRING, email STRING, "
                               "plan STRING, alta DATE, ciudad STRING")
riders = riders.select("rider_id", "plan")
print(">> Riders leídos de HDFS:", riders.count())

# ========== 5. EXPLAIN de una query ==========
# Viajes por plan de un día. Primero el join y DESPUÉS el filtro por fecha:
# Catalyst mueve el filtro antes del join (y hasta la lectura del Parquet)
consulta = (silver.join(riders, "rider_id", "left")
            .filter(F.col("fecha") == "2026-05-26")
            .groupBy("plan").agg(F.count("*").alias("viajes"))
            .orderBy("plan"))
print(">> EXPLAIN de la consulta (viajes por plan del 2026-05-26):")
consulta.explain(True)
consulta.show()

# ========== 6. GOLD: gold_ops_diaria ==========
silver = silver.cache()            # Silver se usa varias veces: lo dejamos en memoria
n_silver_hdfs = silver.count()     # esta línea llena el caché

gold = (silver.groupBy("fecha")
        .agg(F.count("*").alias("viajes"),
             F.round(F.sum("duracion_min"), 2).alias("minutos"),
             F.round(F.sum("km"), 2).alias("km"),
             F.round(F.sum("fare_ars"), 2).alias("ingresos_ars"),
             F.round(100 * F.avg(F.col("clima_adverso").cast("int")), 2).alias("pct_clima_adverso"))
        .orderBy("fecha"))
RUTA_GOLD = HDFS + "/nexo/gold/gold_ops_diaria"
gold.coalesce(1).write.mode("overwrite").parquet(RUTA_GOLD)

gold_leido = spark.read.parquet(RUTA_GOLD)
total = gold_leido.agg(F.sum("viajes")).first()[0]
print(">> Días en gold_ops_diaria:", gold_leido.count())
print(">> G1 sum(viajes) = filas de Silver ?", total, "=", n_silver_hdfs, "->", total == n_silver_hdfs)
print(">> Días sin dato de clima:", gold_leido.filter(F.col("pct_clima_adverso").isNull()).count())
gold_leido.show(10)

# Top 10 estaciones de origen (con el nombre desde estaciones.csv)
estaciones = spark.read.csv("/opt/nexo/data/estaciones.csv", header=True, inferSchema=True)
top10 = (silver.groupBy("station_start").agg(F.count("*").alias("viajes"))
         .join(estaciones.select("station_id", "nombre", "barrio"),
               F.col("station_start") == F.col("station_id"))
         .select("station_id", "nombre", "barrio", "viajes")
         .orderBy(F.col("viajes").desc()).limit(10))
top10.write.mode("overwrite").parquet(HDFS + "/nexo/gold/top_estaciones_origen")
print(">> Top 10 estaciones de origen:")
top10.show()

# Viajes e ingresos por plan de rider (join con riders de M7)
print(">> Viajes e ingresos por plan de rider:")
(silver.join(riders, "rider_id", "left").groupBy("plan")
       .agg(F.count("*").alias("viajes"), F.round(F.sum("fare_ars"), 2).alias("ingresos_ars"))
       .orderBy(F.col("viajes").desc()).show())

spark.stop() 