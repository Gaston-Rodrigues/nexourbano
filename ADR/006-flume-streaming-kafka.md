# ADR 006 — Flume, Structured Streaming y Kafka para eventos en tiempo real

- **Qué se probó:** un agente Flume 1.11.0 (`04-hadoop/flume/agente_logs.conf`) vigila un log y lo escribe en HDFS `/nexo/bronze/logs/`. Con 200 eventos simulados (81 `ride_start`, 94 `ride_end`, 25 `payment_fail`) llegaron los 200 a HDFS (`evidence/flume/`).
- **Flume es una tubería:** mueve datos de un origen (un archivo, un puerto) a un destino (HDFS) solo con configuración, sin código. No transforma ni agrega: lo que entra, sale igual.
- **Structured Streaming es procesamiento:** es el motor de Spark que lee un flujo y calcula sobre él (ventanas de tiempo, watermark, joins, alertas). No recolecta datos: necesita una fuente de donde leer.
- **Kafka es el buffer:** un registro duradero de eventos que varios consumidores pueden leer, y volver a leer si hace falta. Desacopla a quien produce los eventos de quien los consume.
- **La diferencia en una frase:** Flume mueve, Structured Streaming procesa y Kafka retiene y distribuye. No compiten del todo, se combinan.
- **Diseño greenfield 2026:** aplicaciones y agentes → Kafka → Structured Streaming → tablas Parquet o Delta. Flume no entraría en un diseño nuevo.
- **Cuándo sí Flume:** si ya existe y el trabajo es llevar logs a HDFS sin escribir código. La versión que usamos (1.11.0) es de octubre de 2022 y casi no evoluciona; hubo que arreglar a mano la librería `guava` y descargar un JDK para el resto de M7.
- **Límites de lo probado:** el log se simuló copiando 200 líneas de `data/app.log` a un archivo vigilado. El canal es en memoria: si el agente se cae, se pierden los eventos que no se escribieron (no hay durabilidad). No se ejecutó Kafka. 