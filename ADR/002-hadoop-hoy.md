# ADR 002 · Por qué Hadoop sigue en el diseño de NexoUrbano

Estado: aceptado · Fecha: 2026-10-17 · Responsable: Gastón Rodrigues

## Contexto
NexoUrbano guarda viajes, logs y tickets de soporte. Parte de esos datos ya viven (o van a vivir) en HDFS, y hay herramientas que dependen de él: Hive, HBase, Sqoop y Flume. Hay que decidir si Hadoop se queda en el diseño o se reemplaza todo por servicios cloud y Spark.

## Decisión
Se mantiene Hadoop (HDFS y YARN) como **capa batch heredada**. Los trabajos nuevos se escriben en Spark, no en MapReduce.

## Por qué sigue Hadoop
1. **Almacenamiento barato.** HDFS corre en discos comunes y guarda los datos crudos (Bronze) sin pagar por cada consulta ni por cada GB que sale, como pasa en la nube.
2. **Hive y lo heredado.** Hive, HBase, Sqoop y Flume ya están pensados para HDFS. Reemplazarlos tiene un costo de migración que hoy no se justifica.
3. **Cumplimiento.** Los datos de viajes y riders se pueden mantener en infraestructura propia, sin sacarlos a un proveedor externo, si la empresa lo exige.

## Qué no volveríamos a poner en MapReduce en 2026
- **Procesos con varias etapas encadenadas** (limpiar, cruzar, agrupar): cada etapa escribe a disco y es lento. Spark los hace en memoria.
- **Cruces (joins) entre tablas grandes:** en MapReduce se escriben a mano y son largos. En Spark o Hive son una línea.
- **Cualquier cosa casi en tiempo real:** MapReduce trabaja por lotes. Para eso va Spark Structured Streaming.
- **Código nuevo de análisis:** se escribe en Spark. MapReduce queda solo para el conteo de palabras del M5, como ejemplo clásico, y para mantener trabajos viejos.

## Versiones usadas en el sandbox
| Componente | Versión |
|---|---|
| Hadoop (imagen `apache/hadoop:3`) | 3.3.6 |
| Java dentro de la imagen | 1.8 |
| Nodos | 1 NameNode, 2 DataNodes, 1 ResourceManager, 1 NodeManager |
| Replicación de bloques | 2 |

## Consecuencias y límites
- El sandbox corre en una sola PC con Docker. La replicación 2 y los 2 DataNodes sirven para demostrar cómo funciona HDFS, pero no representan un clúster de producción (ahí se usaría replicación 3 o más y varios servidores).
- Hive y HBase se levantan en el M6, y Pig, Sqoop y Flume en el M7.
- Evidencia: `evidence/hadoop/bootstrap.log`.
 