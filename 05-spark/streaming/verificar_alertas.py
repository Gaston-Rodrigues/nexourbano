# verificar_alertas.py - compara gold_alerts (streaming) con un recuento en batch de los archivos originales
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

HDFS = "hdfs://namenode:8020"
spark = (SparkSession.builder.appName("verificar_alertas")
         .config("spark.sql.session.timeZone", "UTC").getOrCreate())
spark.sparkContext.setLogLevel("WARN")

# 1. Lo que guardó el streaming
gold = spark.read.parquet(HDFS + "/nexo/gold/gold_alerts")
print(">> Ventanas guardadas en gold_alerts:", gold.count())
gold.printSchema()
gold.orderBy("window_start", "event").show(10, False)

# 2. Recuento en batch de TODOS los eventos (sin watermark: nada se descarta)
esquema = "ts TIMESTAMP, event STRING, vehicle_id STRING, rider_id STRING, battery_pct DOUBLE"
todos = (spark.read.schema(esquema).option("pathGlobFilter", "eventos_*.json").json("/opt/nexo/data/stream"))
recuento = (todos.filter(F.col("event").isin("payment_fail", "battery_low"))
            .groupBy(F.window("ts", "2 minutes", "30 seconds"), "event").count()
            .select(F.col("window.start").alias("window_start"),
                    F.col("window.end").alias("window_end"),
                    "event", F.col("count").alias("count_batch")))

# 3. Comparar ventana por ventana
comparacion = (gold.join(recuento, ["window_start", "window_end", "event"], "left")
               .withColumn("diferencia", F.col("count_batch") - F.col("count")))

print(">> Ventanas donde el streaming cuenta MENOS que el batch (eventos descartados por el watermark):")
comparacion.filter("diferencia <> 0").orderBy("window_start", "event").show(20, False)
print(">> Ventanas con el mismo conteo en streaming y en batch:", comparacion.filter("diferencia = 0").count())
spark.stop()
