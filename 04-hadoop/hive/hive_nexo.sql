-- hive_nexo.sql — M6: Hive sobre HDFS (NexoUrbano)

-- 1. Base de datos
CREATE DATABASE IF NOT EXISTS nexo;
USE nexo;

-- 2. Tabla EXTERNA: lee el CSV que esta en HDFS, no copia ni mueve los datos
CREATE EXTERNAL TABLE IF NOT EXISTS bronze_viajes (
  ride_id STRING, ts_start STRING, ts_end STRING, duration_s INT,
  rider_id STRING, vehicle_id STRING, station_start STRING, station_end STRING,
  barrio_start STRING, barrio_end STRING,
  lat_start DOUBLE, lon_start DOUBLE, lat_end DOUBLE, lon_end DOUBLE,
  km DOUBLE, fare_ars DOUBLE, clima_codigo INT
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 'hdfs://namenode:8020/nexo/hive/bronze_viajes'
TBLPROPERTIES ('skip.header.line.count'='1');

-- 3. Tabla INTERNA (managed) particionada por fecha (Hive guarda los datos, un directorio por dia)

SET hive.support.concurrency=true;
SET hive.txn.manager=org.apache.hadoop.hive.ql.lockmgr.DbTxnManager;

DROP TABLE IF EXISTS silver_viajes;

CREATE TABLE silver_viajes (
  ride_id STRING, ts_start STRING, ts_end STRING, duration_s INT,
  rider_id STRING, vehicle_id STRING, station_start STRING, station_end STRING,
  barrio_start STRING, barrio_end STRING,
  lat_start DOUBLE, lon_start DOUBLE, lat_end DOUBLE, lon_end DOUBLE,
  km DOUBLE, fare_ars DOUBLE, clima_codigo INT,
  hora_local INT
)
PARTITIONED BY (fecha STRING)
STORED AS ORC
TBLPROPERTIES ('transactional'='true');
-- 4. Cargar Silver desde Bronze (la fecha sale de los primeros 10 caracteres de ts_start)
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;

INSERT OVERWRITE TABLE silver_viajes PARTITION (fecha)
SELECT ride_id, ts_start, ts_end, duration_s,
       rider_id, vehicle_id, station_start, station_end,
       barrio_start, barrio_end,
       lat_start, lon_start, lat_end, lon_end,
       km, fare_ars, clima_codigo,
       pmod(CAST(substr(ts_start, 12, 2) AS INT) - 3, 24) AS hora_local,
       substr(ts_start, 1, 10) AS fecha
FROM bronze_viajes;

-- 5. Controles
SELECT COUNT(*) AS filas_bronze FROM bronze_viajes;
SELECT COUNT(*) AS filas_silver FROM silver_viajes;
SELECT COUNT(DISTINCT fecha) AS dias_particionados FROM silver_viajes;

-- 6. CONSULTA 1: estaciones con mas viajes de llegada (destinos)
SELECT station_end AS estacion, COUNT(*) AS viajes_llegada
FROM silver_viajes
GROUP BY station_end
ORDER BY viajes_llegada DESC
LIMIT 5;

-- 7. CONSULTA 2: viajes de mas de 45 minutos (2700 segundos)
SELECT ride_id, vehicle_id, barrio_start, barrio_end,
       ROUND(duration_s / 60, 1) AS minutos
FROM silver_viajes
WHERE duration_s > 2700
ORDER BY duration_s DESC
LIMIT 10;

-- 8. CONSULTA 3: cantidad de viajes y duracion promedio por hora local y barrio
SELECT hora_local, barrio_start AS barrio,
       COUNT(*) AS viajes,
       ROUND(AVG(duration_s) / 60, 1) AS duracion_prom_min
FROM silver_viajes
GROUP BY hora_local, barrio_start
ORDER BY viajes DESC
LIMIT 15;