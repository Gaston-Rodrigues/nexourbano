#!/bin/bash
# Importa la tabla crm.riders de MySQL a HDFS con Sqoop (M7)
# La contrasena llega en la variable SQOOP_DB_PASS (no se guarda en el repo)
export JAVA_HOME=/opt/jdk8
export HADOOP_COMMON_HOME=/opt/hadoop
export HADOOP_MAPRED_HOME=/opt/hadoop

/opt/sqoop/bin/sqoop import \
  --connect "jdbc:mysql://mysql:3306/crm?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC" \
  --username root \
  --password "$SQOOP_DB_PASS" \
  --table riders \
  --target-dir /nexo/bronze/riders_sqoop \
  --delete-target-dir \
  -m 1