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
- `main` sólo recibe PRs (aunque sean internos) · commits atómicos · tag `entrega-final` al cierre.
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