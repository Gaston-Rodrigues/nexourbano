# P5: facturación por viajes (Spark sobre la tabla Gold)
from pyspark.sql import SparkSession, functions as F

HDFS = "hdfs://namenode:8020"

spark = SparkSession.builder.appName("p5_facturacion").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

gold = spark.read.parquet(HDFS + "/nexo/gold/gold_ops_diaria")
r = gold.agg(F.sum("viajes").alias("viajes"),
             F.round(F.sum("ingresos_ars"), 2).alias("ingresos"),
             F.min("fecha").alias("desde"),
             F.max("fecha").alias("hasta")).first()

print(">> P5 viajes:", r["viajes"], "| ingresos_ars:", r["ingresos"],
      "| desde:", r["desde"], "| hasta:", r["hasta"])
spark.stop()