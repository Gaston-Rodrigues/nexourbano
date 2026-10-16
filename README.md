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
py tools\generar_datos.py --seed 131 --n-viajes 1000000   # si la RAM no da: 250000 y anotarlo en ADR/000
Copy-Item .env.example .env                               # editar contraseñas
py scripts\verificar_entorno.py
```

**2. Servicios** (primera fase: los 5 motores base con un solo comando)
```powershell
docker compose up -d                       # MinIO, MySQL, MongoDB, Cassandra, Neo4j
docker compose ps                          # los 5 en "running"
# Fase 2 (más adelante):  docker compose --profile hadoop up -d   y   --profile spark
```
UIs: MinIO http://localhost:9001 · Neo4j http://localhost:7474 (HDFS 9870, YARN 8088, HBase 16010, Spark 4040 en la fase 2)

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