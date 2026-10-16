# ADR 000 · Contexto del squad

- **Ciudad de operación:** Buenos Aires (generador seed 131)
- **Semilla `--seed`:** 131 · `python tools/generar_datos.py --seed 131 --n-viajes 1000000`
- **Dataset sintético:** 1.000.000 de viajes en `data/viajes.csv`. Perfilado con `01-discovery/perfilado.py` · reporte: `evidence/m1_perfilado_viajes.txt`.
- **Dataset abierto de movilidad:** Citi Bike NYC, septiembre 2026
  - URL: https://s3.amazonaws.com/tripdata/202609-citibike-tripdata.zip
  - Fecha de descarga: 2026-10-15
  - Perfilado sobre la parte 1 (`202609-citibike-tripdata_1.csv`): 1.000.000 filas, fechas 2026-08-31 a 2026-09-14.
  - Script: `01-discovery/perfilado_abierto.py` · reporte: `evidence/m1_perfilado_citibike.txt`
  - Hallazgos: 0 `ride_id` duplicados; ~0,2 % de nulos en estaciones y coordenadas;
    duración mínima 60 s (viene filtrado de origen); 733 viajes de más de 4 h (0,07 %).
- **Entorno:** local con Docker Compose (16 GB RAM). Data Lake = MinIO (Plan B de ADLS Gen2, ver ADR 001).
- **Hardware:** 16 GB RAM → 1 M de viajes factible; si Spark se queda sin memoria se baja a 250 k y se anota acá.

## Owners por módulo
Squad de 1 integrante: Gastón Rodrigues es owner de todos los módulos y no tiene backup.

| Módulo | Owner | Backup |
|---|---|---|
| Discovery / 4 V | Gastón Rodrigues | — |
| Azure Data Lake / MinIO | Gastón Rodrigues | — |
| Databricks / APIs | Gastón Rodrigues | — |
| Hadoop (HDFS, MR, Hive, HBase, Pig, Sqoop, Flume) | Gastón Rodrigues | — |
| Spark batch + streaming | Gastón Rodrigues | — |
| MongoDB | Gastón Rodrigues | — |
| Cassandra | Gastón Rodrigues | — |
| Neo4j | Gastón Rodrigues | — |
| Producto Gold + demo | Gastón Rodrigues | — |

## Recortes de alcance (con la sección del enunciado que los autoriza)
Ninguno por ahora. Si hay que recortar, sólo los de la sección 8 del enunciado y con ADR.