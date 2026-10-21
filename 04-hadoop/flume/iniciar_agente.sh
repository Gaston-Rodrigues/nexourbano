#!/bin/bash
# Arranca el agente Flume a1 (vigila /tmp/app_vivo.log y escribe en HDFS)
export JAVA_HOME=/opt/jdk8
rm -f /tmp/app_vivo.log /tmp/flume_taildir_pos.json
touch /tmp/app_vivo.log
/opt/flume/bin/flume-ng agent --conf /opt/flume/conf --conf-file /work/04-hadoop/flume/agente_logs.conf --name a1 -Dflume.root.logger=INFO,console