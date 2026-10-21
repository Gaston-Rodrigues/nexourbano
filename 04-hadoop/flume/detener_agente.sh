#!/bin/bash
# Detiene el agente Flume a1
PID=$(ps -ef | grep '[o]rg.apache.flume.node.Application' | awk '{print $2}')
if [ -n "$PID" ]; then
  kill $PID
fi
sleep 2
echo "Procesos de Flume que siguen vivos: $(ps -ef | grep -c '[o]rg.apache.flume.node.Application')"