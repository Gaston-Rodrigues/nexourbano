# ADR 004 — Pig para limpiar viajes y por qué en 2026 se usaría Spark

- **Contexto:** hay que limpiar `viajes_muestra.csv` (2000 viajes en HDFS): descartar duraciones menores a 30 s o mayores a 4 h y marcar la distancia nula. El script es `04-hadoop/pig/clean_viajes.pig` y escribe `clean_viajes` en `/nexo/silver/clean_viajes`.
- **Resultado medido:** entraron 2000 viajes y quedaron 1959. Se descartaron 41: 31 de menos de 30 s y 10 de 20.000 s (los outliers que ya vimos en M1 y en Hive). De los 1959, 79 tienen distancia nula. Se verificó contando por separado sobre el CSV (`evidence/pig/verificacion.txt`).
- **Definición propia de "distancia nula":** salida y llegada en la misma estación (`station_start == station_end`). No se usó `km = 0` porque ningún viaje lo cumple (el mínimo es 0,026 km) y el campo habría salido siempre vacío.
- **Mismo trabajo en Spark** (duplicado a propósito, 7 líneas útiles contra 14 de Pig):

```python
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("clean_viajes").getOrCreate()
viajes = spark.read.csv("hdfs://namenode:8020/nexo/bronze/viajes/viajes_muestra.csv",
                        header=True, inferSchema=True)
validos = viajes.filter((F.col("duration_s") >= 30) & (F.col("duration_s") <= 14400))
clean = validos.withColumn("distancia_nula",
                           (F.col("station_start") == F.col("station_end")).cast("int"))
clean.write.mode("overwrite").csv("hdfs://namenode:8020/nexo/silver/clean_viajes_spark", header=True)
print(viajes.count(), clean.count(), clean.filter("distancia_nula = 1").count())
```

- **Qué dejaríamos en producción 2026: Spark.** Pig no tiene versiones nuevas desde 2017 (0.17.0) y tuvo que adaptarse a mano a Hadoop 3: el contenedor no traía `which`, y sin servidor de historial de trabajos cada conteo esperó unos 3 minutos (el script completo tardó 11 minutos). Spark lee el encabezado solo, infiere tipos, se puede probar y es el mismo motor que usamos para Silver y Gold.
- **Cuándo sí tendría sentido Pig:** solo si ya existen scripts Pig heredados que funcionan y migrarlos cuesta más que mantenerlos.
- **Límite:** el código Spark de este ADR está escrito pero **todavía no se ejecutó**. Se corre cuando levantemos Spark en M8 y se compara que dé 2000, 1959 y 79.