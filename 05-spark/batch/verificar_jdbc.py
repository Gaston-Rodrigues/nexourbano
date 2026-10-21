# Plan B del ADR 005: traer riders desde MySQL con Spark (sin Sqoop)
import os
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("riders_jdbc").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

# Leer la tabla riders directo desde MySQL. La contraseña viene de una variable de entorno
riders = (spark.read.format("jdbc")
          .option("url", "jdbc:mysql://mysql:3306/crm?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC")
          .option("driver", "com.mysql.cj.jdbc.Driver")
          .option("dbtable", "riders")
          .option("user", "root")
          .option("password", os.environ["MYSQL_ROOT_PASSWORD"])
          .load())

# Guardar en HDFS (en otra carpeta, para no pisar la de Sqoop)
riders.write.mode("overwrite").csv("hdfs://namenode:8020/nexo/bronze/riders_spark")

# Comparar con lo que importó Sqoop (tienen que ser 120 filas las dos)
sqoop = spark.read.csv("hdfs://namenode:8020/nexo/bronze/riders_sqoop")
riders.printSchema()
print(">> Riders por JDBC (Spark):", riders.count())
print(">> Riders por Sqoop:", sqoop.count())
spark.stop()