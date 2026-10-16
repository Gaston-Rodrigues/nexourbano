# Arquitectura medallion de NexoUrbano

```mermaid
flowchart LR
  subgraph F[Fuentes]
    A1[Dataset abierto de bici pública<br/>CSV] 
    A2[Open-Meteo<br/>API REST]
    A3[Bluesky / Mastodon<br/>API JSON]
    A4[Generador seed 131<br/>CSV · JSON · logs · SQL]
    A5[(MySQL crm.riders)]
  end
  subgraph B[BRONZE · crudo e inmutable]
    B1[(MinIO/ADLS bronze/<br/>HDFS /nexo/bronze)]
  end
  subgraph S[SILVER · validado y tipado]
    S1[(Parquet particionado<br/>viajes · clima · social)]
  end
  subgraph G[GOLD · decisión]
    G1[gold_ops_diaria<br/>gold_alerts]
  end
  A1 & A2 & A3 & A4 --> B1
  A5 -- Sqoop / Spark JDBC --> B1
  A4 -- Flume / streaming --> B1
  B1 -- "Spark batch + reglas de contrato" --> S1
  S1 --> G1
  S1 --> HV[Hive SQL]
  G1 --> HB[HBase: estado de flota]
  A4 --> CA[(Cassandra: lecturas por vehículo)]
  A4 --> MO[(MongoDB: catálogo y ventas)]
  A4 --> NE[(Neo4j: grafo social)]
  G1 & CA & MO & NE --> P[09-producto/decision_ops.py<br/>5 preguntas de negocio]
```

## Qué motor ancla cada V

| V | Motor(es) | Por qué ese motor |
|---|---|---|
| **Volumen** | HDFS + MinIO/ADLS (almacenamiento) · Spark batch (cómputo) | Almacenamiento barato y particionado; cómputo distribuido para 1 M de viajes |
| **Variedad** | MongoDB (catálogo anidado) · Hive (schema-on-read sobre CSV) · MapReduce (texto) | Cada formato en el motor que lo modela sin forzarlo |
| **Velocidad** | Spark Structured Streaming (ventanas) · Cassandra (escritura sostenida, último estado) · Flume (ingesta de logs) | Latencia de segundos y escrituras constantes por vehículo |
| **Veracidad** | Contratos YAML + reglas en Spark (Silver) + cuarentena (DLQ) + watermark | La calidad es código, versionado y medido (ver `evidence/m1_perfilado_*.txt`) |
| **Complejidad** | Neo4j (relaciones y fraude) · HBase (rowkey salada, acceso por clave) · Cassandra (modelo por query) | La decisión de modelado ya viene dada por el patrón de consulta |

## Una carga de trabajo por motor
Series de tiempo → Cassandra · Catálogo → MongoDB · Relaciones → Neo4j · SQL analítico → Hive/Spark ·
Serving por clave → HBase · Landing → MinIO/ADLS · Legado batch → HDFS/MapReduce/Pig/Sqoop/Flume.
Las justificaciones de 5 líneas están en `ADR/`.
