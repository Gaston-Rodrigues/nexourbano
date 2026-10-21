-- clean_viajes.pig - limpia los viajes y marca la distancia nula (M7)

-- Si ya existe la salida de una corrida anterior, se borra
rmf /nexo/silver/clean_viajes;

-- 1. Leer los viajes desde HDFS
viajes = LOAD '/nexo/bronze/viajes/viajes_muestra.csv' USING PigStorage(',')
         AS (ride_id:chararray, ts_start:chararray, ts_end:chararray, duration_s:int,
             rider_id:chararray, vehicle_id:chararray,
             station_start:chararray, station_end:chararray,
             barrio_start:chararray, barrio_end:chararray,
             lat_start:double, lon_start:double, lat_end:double, lon_end:double,
             km:double, fare_ars:double, clima_codigo:int);

-- 2. Sacar la fila del encabezado
sin_encabezado = FILTER viajes BY ride_id != 'ride_id';

-- 3. Sacar duraciones absurdas: menos de 30 segundos o mas de 4 horas (14400 s)
validos = FILTER sin_encabezado BY duration_s >= 30 AND duration_s <= 14400;

-- 4. Distancia nula = sale y llega a la misma estacion (1 si, 0 no)
clean_viajes = FOREACH validos GENERATE *,
               (station_start == station_end ? 1 : 0) AS distancia_nula;

-- 5. Guardar el resultado en HDFS
STORE clean_viajes INTO '/nexo/silver/clean_viajes' USING PigStorage(',');

-- 6. Conteos para la evidencia
g_entrada = GROUP sin_encabezado ALL;
n_entrada = FOREACH g_entrada GENERATE 'viajes_entrada' AS etiqueta, COUNT(sin_encabezado) AS n;
g_limpios = GROUP clean_viajes ALL;
n_limpios = FOREACH g_limpios GENERATE 'viajes_limpios' AS etiqueta, COUNT(clean_viajes) AS n;
nulas = FILTER clean_viajes BY distancia_nula == 1;
g_nulas = GROUP nulas ALL;
n_nulas = FOREACH g_nulas GENERATE 'distancia_nula' AS etiqueta, COUNT(nulas) AS n;
DUMP n_entrada;
DUMP n_limpios;
DUMP n_nulas;