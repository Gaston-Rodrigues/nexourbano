@echo off
echo === ANTES: datos de cada tabla en HDFS ===
echo --- bronze_viajes (externa): archivos en su carpeta
docker exec nexo-namenode hdfs dfs -ls /nexo/hive/bronze_viajes
echo --- silver_viajes (interna): directorios, archivos y bytes
docker exec nexo-namenode hdfs dfs -count /user/hive/warehouse/nexo.db/silver_viajes
echo.
echo === DROP de la tabla externa bronze_viajes y de la interna silver_viajes ===
docker exec nexo-hive beeline -u jdbc:hive2://localhost:10000 -e "DROP TABLE nexo.bronze_viajes; DROP TABLE nexo.silver_viajes;"
echo.
echo === DESPUES: datos de cada tabla en HDFS ===
echo --- bronze_viajes (externa): el CSV tiene que seguir ahi
docker exec nexo-namenode hdfs dfs -ls /nexo/hive/bronze_viajes
echo --- silver_viajes (interna): tiene que haber desaparecido
docker exec nexo-namenode hdfs dfs -count /user/hive/warehouse/nexo.db/silver_viajes
echo === FIN ===