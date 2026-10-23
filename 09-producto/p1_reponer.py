# P1: ¿Dónde reponer scooters en las próximas 3 h si llueve?
# Motor: Spark (Silver con clima) + estaciones.csv
import sys
from pyspark.sql import SparkSession, functions as F

HDFS = "hdfs://namenode:8020"

# Hora local de inicio de la franja (por defecto 8). Se recibe como argumento.
hora_ini = int(sys.argv[1]) if len(sys.argv) > 1 else 8
horas = [(hora_ini + i) % 24 for i in range(3)]

spark = SparkSession.builder.appName("p1_reponer").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

silver = spark.read.parquet(HDFS + "/nexo/silver/viajes")
estaciones = spark.read.csv("/opt/nexo/data/estaciones.csv", header=True)

# Solo viajes con lluvia (weather_code >= 51) dentro de la franja
lluvia = silver.filter(F.col("clima_adverso") & F.col("hora").isin(horas))
dias_con_lluvia = lluvia.select("fecha").distinct().count()

print(">> P1 franja local:", horas, "| días con lluvia en esa franja:", dias_con_lluvia)

if dias_con_lluvia == 0:
    print(">> P1 FALTA DATO: no hay viajes con lluvia en esa franja, no se puede rankear")
else:
    top = (lluvia.groupBy("station_start").agg(F.count("*").alias("salidas"))
           .join(estaciones.select("station_id", "nombre", "barrio"),
                 F.col("station_start") == F.col("station_id"))
           .withColumn("salidas_por_dia_lluvia",
                       F.round(F.col("salidas") / dias_con_lluvia, 2))
           .orderBy(F.desc("salidas"))
           .limit(5))
    for f in top.collect():
        print(">> P1", f["station_start"], f["nombre"], f["barrio"],
              "salidas:", f["salidas"], "por día con lluvia:", f["salidas_por_dia_lluvia"])

print(">> P1 LIMITE: no hay stock actual por estación ni pronóstico; se usa el histórico")
spark.stop()