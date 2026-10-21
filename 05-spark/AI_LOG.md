# AI_LOG · 05-spark

| Fecha | Prompt (resumen) | Qué se aceptó | Qué se corrigió a mano | Qué falló |
|---|---|---|---|---|
| 2026-10-21 | Construimos juntos, con Claude como guía: job Spark Bronze→Silver→Gold (gold_ops_diaria), explain de una consulta y ejecución del código de los ADR 004 y 005 | job_gold.py, descargar_clima.py, verificar_pig_spark.py, verificar_jdbc.py y ADR 007 | Nombres y rutas de los archivos, y los ADR 004 y 005 con lo realmente ejecutado | verificar_jdbc.py falló con "No suitable driver"; se corrigió agregando la opción driver |