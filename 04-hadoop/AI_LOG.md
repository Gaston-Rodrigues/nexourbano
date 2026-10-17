# AI_LOG · 04-hadoop

| Fecha | Prompt (resumen) | Qué se aceptó | Qué se corrigió a mano | Qué falló |
|---|---|---|---|---|
| 17/10/2026 | Levantar Hadoop con Docker, log de HDFS, quiz de 4 V y ADR 002 | Estructura del ADR y del quiz, y comandos para levantar y formatear el NameNode | Construimos la solución juntos y probé cada paso | El NameNode se reiniciaba en bucle: carpeta de solo lectura, rutas de otro usuario y disco sin formatear |
| 17/10/2026 | Comandos de HDFS, prueba de caída de un DataNode y WordCount sobre los tickets de soporte | Comandos de HDFS y del job de MapReduce, y la forma de limpiar el top 20 | Construimos todo juntos y probé cada paso | Comando con `head` que no existe en Windows. WordCount crudo con palabras vacías, hashtags y mayúsculas mezcladas |