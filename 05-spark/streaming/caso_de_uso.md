# Caso de uso: alerta de flota caída

1. **Problema:** el ops manager necesita enterarse en menos de un minuto de que la flota se está cayendo (muchas baterías bajas o muchos pagos fallidos a la vez), antes de que los riders lo reclamen.
2. **Señal:** `gold_alerts` cuenta `battery_low` y `payment_fail` en ventanas de 2 minutos que avanzan cada 30 segundos.
3. **Regla de alerta (propuesta, no implementada):** si en una ventana `battery_low` supera el doble de su promedio, hay posible falta de carga; si sube `payment_fail`, hay posible falla del cobro o fraude.
4. **Acción:** ops manda un equipo a recargar las estaciones afectadas, o escala el problema al equipo de pagos.
5. **Por qué streaming:** un reporte batch diario avisaría horas tarde; la ventana deslizante da una respuesta nueva cada 30 segundos.
6. **Límites:** los datos son simulados; un vehículo sin señal puede reportar con más de 1 minuto de retraso y el watermark lo descarta; los umbrales hay que calibrarlos con datos reales.
