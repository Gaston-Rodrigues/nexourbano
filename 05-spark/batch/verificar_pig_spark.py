# Mismo trabajo que clean_viajes.pig (ADR 004), pero con Spark.
# Tiene que dar lo mismo que Pig: 2000 entraron, 1959 quedaron, 79 con distancia nula.
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("clean_viajes").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

# Leer la muestra de 2000 viajes que está en HDFS
viajes = spark.read.csv("hdfs://namenode:8020/nexo/bronze/viajes/viajes_muestra.csv",
                        header=True, inferSchema=True)

# Quedarnos con duraciones entre 30 s y 4 horas
validos = viajes.filter((F.col("duration_s") >= 30) & (F.col("duration_s") <= 14400))

# Marcar distancia nula: salida y llegada en la misma estación
clean = validos.withColumn("distancia_nula",
                           (F.col("station_start") == F.col("station_end")).cast("int"))

# Guardar el resultado en HDFS (en otra carpeta, para no pisar la de Pig)
clean.write.mode("overwrite").csv("hdfs://namenode:8020/nexo/silver/clean_viajes_spark", header=True)

print(">> Spark (entraron, quedaron, distancia_nula):",
      viajes.count(), clean.count(), clean.filter("distancia_nula = 1").count())
spark.stop()