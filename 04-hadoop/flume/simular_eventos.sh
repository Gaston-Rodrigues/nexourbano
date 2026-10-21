#!/bin/bash
# Agrega 200 eventos (ride_start, ride_end, payment_fail) de a poco al log que vigila Flume
grep -E '"event": "(ride_start|ride_end|payment_fail)"' /datos/app.log | head -200 | while read linea; do
  echo "$linea" >> /tmp/app_vivo.log
  sleep 0.05
done
echo "Eventos agregados: $(wc -l < /tmp/app_vivo.log)"