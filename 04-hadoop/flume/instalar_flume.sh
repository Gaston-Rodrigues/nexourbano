#!/bin/bash
# Instala Apache Flume 1.11.0 dentro del contenedor del NameNode (si todavia no esta)
if [ ! -d /opt/flume ]; then
  cd /tmp
  # Se descarga del espejo principal; si falla, del archivo historico. Con limite de tiempo y reintentos
  curl -fsSL --retry 3 --connect-timeout 30 --max-time 900 -o flume.tar.gz https://dlcdn.apache.org/flume/1.11.0/apache-flume-1.11.0-bin.tar.gz \
  || curl -fsSL --retry 3 --connect-timeout 30 --max-time 1800 -o flume.tar.gz https://archive.apache.org/dist/flume/1.11.0/apache-flume-1.11.0-bin.tar.gz
  tar -xzf flume.tar.gz
  mv apache-flume-1.11.0-bin /opt/flume
  rm flume.tar.gz
  # Flume trae una guava vieja que choca con la de Hadoop 3: se reemplaza por la de Hadoop
  rm /opt/flume/lib/guava-*.jar
  cp /opt/hadoop/share/hadoop/common/lib/guava-*.jar /opt/flume/lib/
fi
ls /opt/flume/lib | grep guava
/opt/flume/bin/flume-ng version 