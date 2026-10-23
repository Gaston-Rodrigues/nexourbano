# NexoUrbano · Lakehouse operacional de micromovilidad (squad seed 131)

Plataforma de datos Bronze → Silver → Gold con evidencia ejecutable de cada motor
(HDFS, MapReduce, Hive, HBase, Pig, Sqoop, Flume, Spark batch/streaming, MongoDB, Cassandra, Neo4j).

> **Demo de 8 minutos:** _(pegar link al terminar)_

## Levantar todo en < 20 minutos (Windows 10 + Docker Desktop, 16 GB RAM)

**0. Memoria para Docker (una sola vez).** Crear `C:\Users\<vos>\.wslconfig`:
```ini
[wsl2]
memory=10GB
processors=4
swap=4GB
```
y reiniciar con `wsl --shutdown`.

**1. Datos y secretos**
```powershell
py tools\generar_datos.py --seed 131 --n-viajes 1000000
Copy-Item .env.example .env
py scripts\verificar_entorno.py
```
Después de copiar `.env.example`, editar las contraseñas de `.env`.

**2. Servicios**
```powershell
docker compose up -d
docker compose ps
```
Con ese comando arrancan los motores base: MinIO, MySQL, MongoDB, Cassandra y Neo4j. Hadoop, Hive y HBase se activan con un perfil:
```powershell
docker compose --profile hadoop up -d
```
Ese perfil agrega NameNode, 2 DataNodes, ResourceManager, NodeManager, Hive y HBase. El perfil `spark` se usa más adelante (Spark batch y streaming).

| Interfaz | Dirección |
|---|---|
| MinIO | http://localhost:9001 |
| Neo4j | http://localhost:7474 |
| HDFS (NameNode) | http://localhost:9870 |
| YARN (ResourceManager) | http://localhost:8088 |
| HBase (Master) | http://localhost:16010 |
| Spark (perfil `spark`) | http://localhost:4040 |

**3. Capturar evidencia sin ruido de PowerShell** (usar `cmd /c`, evita el `NativeCommandError`):
```powershell
cmd /c "docker compose exec -T namenode hdfs dfs -ls -R /nexo > evidence\hadoop\hdfs_ls.log 2>&1"
```
La evidencia es **salida real pegada tal cual**: si un comando falla, el error se queda en el log y se anota cómo se arregló.

## Reglas del repo
- Commits atómicos (uno por módulo) · tag `entrega-final` al cierre.
- Secretos sólo en `.env` (ignorado). `data/` < 20 MB: lo grande se regenera con la semilla.
- Contratos como código: `py tools\validar_contratos.py` debe dar 0 errores.
- IA: cada sesión relevante se anota en `AI_LOG.md` (qué se aceptó, qué se corrigió, qué falló). Hay que poder explicar cada línea.
- Un motor, una carga de trabajo; justificación de 5 líneas por motor en `ADR/`.

## Data lake (M2)

Data lake local con MinIO (compatible con S3). Los viajes crudos están en:

- **URI:** `s3a://bronze/viajes/2026/10/15/viajes.csv`
- **Consola web:** http://localhost:9001
- Evidencia: `evidence/azure/03_minio_bronze_viajes.webp`

## Notas de operación (Hadoop, Hive y HBase)

- **Apagar sin perder datos:** `docker compose --profile hadoop stop`. No usar `down -v`: borra los volúmenes y con ellos los datos de HDFS.
- **HBase:** `py 04-hadoop\hbase\preparar_vehiculos.py` genera los comandos de carga. La primera vez se ejecutan con:
```powershell
  docker exec nexo-hbase hbase shell /work/04-hadoop/hbase/cargar_vehiculos.txt
```
- **Hive:** el metastore (Derby) vive dentro del contenedor; los datos reales están en HDFS. Las tablas se crean con:
```powershell
  docker exec nexo-hive beeline -u jdbc:hive2://localhost:10000 -f /work/04-hadoop/hive/hive_nexo.sql
```
- **Si Hive entra en bucle de reinicios después de un `stop`** (queda un archivo de control viejo dentro del contenedor):
```powershell
  docker rm -f nexo-hive
  docker exec nexo-namenode hdfs dfs -rm -r -f /user/hive/warehouse/nexo.db
  docker compose --profile hadoop up -d hive
```
  y volver a ejecutar `hive_nexo.sql`.

## Alcance y límites conocidos

- **Squad de un integrante** (Gastón Rodrigues). Los datos son sintéticos (seed 131, ver `data/MANIFIESTO.txt`).
- **Data lake con MinIO en lugar de Azure** (ver `ADR/001-datalake.md`). Azure no se midió.
- **HDFS y Hive trabajan con la muestra** `viajes_muestra.csv` (2000 viajes), que el manifiesto indica para HDFS. El millón de viajes se procesa en Databricks y en Spark.
- **Los 2 DataNodes corren en la misma PC**: la caída de un nodo es simulada. HBase corre en un solo servidor (standalone) y el metastore de Hive es Derby embebido. En producción serían servidores distintos.
- **Valores atípicos conocidos:** 10 viajes de la muestra duran exactamente 20.000 s (ver `evidence/m1_perfilado_viajes.txt`).
- **Memoria:** hasta M6 Docker Desktop corrió con el valor por defecto (unos 7,7 GB).

## Spark batch (M8): Bronze → Silver → Gold

Requiere `--profile hadoop` y `--profile spark` arriba y el CSV de viajes en HDFS (`/nexo/bronze/viajes`).
```powershell
docker exec -e HADOOP_USER_NAME=hadoop nexo-spark /opt/spark/bin/spark-submit --master local[*] --driver-memory 2g /opt/nexo/05-spark/batch/job_gold.py
```
Procesa el millón de viajes con reglas de calidad R1 a R5, une el clima y escribe Silver (Parquet particionado por fecha) y Gold (`gold_ops_diaria`, `top_estaciones_origen`) en HDFS. Evidencia: `evidence/spark/job_gold.log`. Decisión: `ADR/007-spark-parquet-gold.md`.

## Spark Streaming (M9): alertas con ventanas y watermark

Ventana de 2 min, slide de 30 s, watermark de 1 min (`ADR/008-streaming-ventanas-watermark.md`). Entre corridas hay que borrar el checkpoint y la salida:
```powershell
docker exec nexo-namenode hdfs dfs -rm -r -f /nexo/checkpoints/gold_alerts /nexo/gold/gold_alerts
docker exec -d nexo-spark bash -c "python3 /opt/nexo/05-spark/streaming/generador_stream.py > /opt/nexo/evidence/spark/generador_stream.log 2>&1"
docker exec -e HADOOP_USER_NAME=hadoop nexo-spark bash -c "/opt/spark/bin/spark-submit --master local[*] /opt/nexo/05-spark/streaming/job_alertas.py 2>&1 | tee /opt/nexo/evidence/spark/streaming_consola.log"
```
La corrida completa dura unos 6 minutos; una captura de 30 s está en `evidence/spark/`. Caso de uso: `05-spark/streaming/caso_de_uso.md`.

## MongoDB (M10 y M11)

```powershell
docker exec nexo-mongo mongosh --quiet /work/06-mongodb/crud.js
docker exec nexo-mongo mongosh --quiet /work/06-mongodb/cargar_ventas.js
docker exec nexo-mongo mongosh --quiet /work/06-mongodb/ventas_pipeline.js
```
CRUD, índice medido (`06-mongodb/indice.md`), comparativa SQL vs documento y aggregation pipeline cuyo resultado queda en `09-producto/ventas_agg.json`.

## Cassandra (M12)

```powershell
docker exec nexo-cassandra cqlsh -f /work/07-cassandra/schema.cql
docker exec nexo-cassandra cqlsh -f /work/07-cassandra/cargar_lecturas.cql
docker exec nexo-cassandra cqlsh -f /work/07-cassandra/queries.cql
```
Tabla modelada por consulta (`PRIMARY KEY ((vehicle_id), ts)` con `ts DESC`), RF=1 en el sandbox, y la consulta anti-patrón que falla a propósito. Decisión: `ADR/009-cassandra-consistencia.md`.

## Neo4j (M13)

```powershell
docker exec nexo-neo4j bash /work/08-neo4j/correr_cypher.sh /work/08-neo4j/grafo.cypher
docker exec nexo-neo4j bash /work/08-neo4j/correr_cypher.sh /work/08-neo4j/queries.cypher
```
Grafo de riders, intereses y estaciones; 4 consultas (amigos en común, camino más corto, recomendación, patrón de fraude). Captura del grafo: `evidence/neo4j/grafo_r0100.png`.

## Producto Gold (M14): decision_ops

Con todos los motores arriba:
```powershell
py -X utf8 09-producto\decision_ops.py
```
Responde 5 preguntas de negocio consultando Spark, Cassandra, MongoDB, Neo4j y HDFS, e indica en cada una qué dato faltó. Resumen: `09-producto/decision_ops.md`. Salida real: `evidence/producto/decision_ops.log`. 

## Recorte de la demo (8 minutos)

| Tiempo | Segmento | Qué se muestra | Evidencia |
|---|---|---|---|
| 0:00 a 0:45 | 1. Problema de negocio | NexoUrbano: micromovilidad con flota, clima y cobros; qué decisiones necesita un ops manager | `01-discovery/acta_discusion.md` |
| 0:45 a 1:45 | 2. Arquitectura y 4 V | Tres fichas 4 V y Bronze, Silver, Gold; cada V ancla un motor | `01-discovery/4V.md`, `01-discovery/arquitectura.md`, `contratos/` |
| 1:45 a 3:15 | 3. Ingesta lakehouse | MinIO (plan B de Azure) y Databricks: clima Open-Meteo, Mastodon y tabla Silver clima × viajes | `ADR/001-datalake.md`, `evidence/azure/`, `03-databricks/01_ingesta.html` |
| 3:15 a 4:45 | 4. Hadoop que todavía paga | HDFS, WordCount de tickets, Hive externa vs interna, HBase, y Pig, Sqoop y Flume frente a Spark | `evidence/hadoop`, `evidence/hive`, `ADR/002` a `ADR/006` |
| 4:45 a 6:15 | 5. Spark batch + streaming | Un millón de viajes a Gold con `explain`; alertas en ventana de 2 min con watermark de 1 min | `evidence/spark/`, `ADR/007`, `ADR/008` |
| 6:15 a 7:45 | 6. Polyglot | Mongo (índice medido), Cassandra (query anti-patrón) y Neo4j (camino más corto), una query de cada uno | `evidence/mongodb`, `evidence/cassandra`, `evidence/neo4j`, `ADR/009` |
| 7:45 a 8:30 | 7. Métricas Gold y decisión | `decision_ops.py` con las 5 preguntas y qué decidiría un ops manager mañana | `09-producto/decision_ops.md`, `evidence/producto/decision_ops.log` |