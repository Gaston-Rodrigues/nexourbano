# ADR 005 — Sqoop para traer el CRM de MySQL a HDFS

- **Contexto:** los datos de riders viven en MySQL (`crm.riders`, 120 filas) y hay que llevarlos a HDFS (`/nexo/bronze/riders_sqoop/`) como capa Bronze, para usarlos después en el join de Spark.
- **Qué se hizo:** Sqoop 1.4.7 importó la tabla con `04-hadoop/sqoop/importar_riders.sh`. Resultado: 120 registros, 8.232 bytes, en 10,6 s (`evidence/sqoop/`). La contraseña se pasa por variable de entorno y no queda en el repo ni en los logs.
- **Lo que hubo que agregar a mano:** un JDK 8 (el contenedor solo trae el JRE y Sqoop necesita `javac`), el driver JDBC de MySQL y `commons-lang` (Hadoop 3 ya no lo trae). Se usa `-m 1` porque la clave primaria es de texto y Sqoop reparte por rangos numéricos.
- **Por qué Sqoop aparece en RFPs viejos:** fue el estándar de los años 2010 para mover tablas relacionales a Hadoop y muchos bancos y telcos tienen cientos de jobs escritos con él. Apache lo retiró (Attic) en 2021 y su última versión (1.4.7, de 2017) es de la era de Hadoop 2. Lo que se entrega es la tabla en HDFS, no el logo de Sqoop.
- **Plan B y diseño 2026:** `spark.read.jdbc` hace lo mismo con menos piezas. Código (escrito, **todavía no ejecutado**; se corre en M8 con Spark):

```python
import os
riders = (spark.read.format("jdbc")
          .option("url", "jdbc:mysql://mysql:3306/crm")
          .option("dbtable", "riders")
          .option("user", "root")
          .option("password", os.environ["MYSQL_ROOT_PASSWORD"])
          .load())
riders.write.mode("overwrite").csv("hdfs://namenode:8020/nexo/bronze/riders_spark")
```

- **Límite:** se usó el usuario `root` por simplicidad del sandbox. En producción corresponde un usuario de solo lectura, idealmente sobre una réplica, y para cambios continuos una herramienta de CDC en lugar de cargas completas.