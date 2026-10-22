# job_alertas.py - M9: alertas por ventana de tiempo con Structured Streaming
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

CARPETA_ENTRADA = "/opt/nexo/data/stream"
HDFS = "hdfs://namenode:8020"
RUTA_GOLD = HDFS + "/nexo/gold/gold_alerts"
RUTA_CHECKPOINT = HDFS + "/nexo/checkpoints/gold_alerts"
DURACION_SEGUNDOS = 360   # el job se apaga solo a los 6 minutos

spark = (SparkSession.builder.appName("job_alertas")
         .config("spark.sql.session.timeZone", "UTC")
         .config("spark.sql.shuffle.partitions", "4")
         .getOrCreate())
spark.sparkContext.setLogLevel("WARN")

# 1. LEER: Spark mira la carpeta y toma cada archivo JSON nuevo que aparece.
#    El esquema es el parseo del JSON: ts, event, vehicle_id, rider_id, battery_pct
esquema = "ts TIMESTAMP, event STRING, vehicle_id STRING, rider_id STRING, battery_pct DOUBLE"
# Solo se leen los eventos_*.json que suelta el generador (los event_000.json del dataset no entran)
eventos = (spark.readStream.schema(esquema)
           .option("pathGlobFilter", "eventos_*.json")
           .json(CARPETA_ENTRADA))

# 2. CONTAR: ventana de 2 minutos que avanza cada 30 segundos, por tipo de evento.
#    withWatermark: se aceptan eventos con hasta 1 minuto de retraso; los más viejos se descartan
alertas = (eventos
           .filter(F.col("event").isin("payment_fail", "battery_low"))
           .withWatermark("ts", "1 minute")
           .groupBy(F.window("ts", "2 minutes", "30 seconds"), "event")
           .count())

# Columnas del contrato gold_alerts.yaml
salida = alertas.select(F.col("window.start").alias("window_start"),
                        F.col("window.end").alias("window_end"),
                        "event", "count")

# 3. SALIDA 1 - consola (update): muestra solo las ventanas que cambiaron en cada tanda
consola = (salida.writeStream.outputMode("update").format("console")
           .option("truncate", "false").option("numRows", 30)
           .trigger(processingTime="10 seconds").start())

# 4. SALIDA 2 - Parquet en HDFS (append): guarda cada ventana cuando ya está cerrada
gold = (salida.writeStream.outputMode("append").format("parquet")
        .option("path", RUTA_GOLD).option("checkpointLocation", RUTA_CHECKPOINT)
        .trigger(processingTime="10 seconds").start())

# Esperar los 6 minutos y apagar
spark.streams.awaitAnyTermination(DURACION_SEGUNDOS)
consola.stop()
gold.stop()
print(">> Fin del streaming")
spark.stop()
 