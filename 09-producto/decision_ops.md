# Producto Gold · NexoUrbano decision_ops

Una sola historia de decisión: `decision_ops.py` consulta 5 motores en vivo y responde 5 preguntas de negocio.
La salida real está en `evidence/producto/decision_ops.log`.

Cómo correrlo (desde la raíz del repo, con los contenedores arriba):

    py -X utf8 09-producto\decision_ops.py        # las 5 preguntas
    py -X utf8 09-producto\decision_ops.py p3     # una sola pregunta

## Supuestos nuestros (el TP no los define)

- Umbral de retiro por batería: SOH < 70 (constante `UMBRAL_SOH`).
- Rider objetivo para la recomendación: R0100 (constante `RIDER_OBJETIVO`).
- "Próximas 3 h": la hora actual de Buenos Aires y las dos siguientes.

## Respuestas

| # | Pregunta | Motores | Respuesta | Dato que faltó |
|---|---|---|---|---|
| 1 | ¿Dónde reponer scooters en las próximas 3 h si llueve? | Spark (Silver con clima) + estaciones | Con lluvia entre 19 y 21 h: ST014 San Telmo (613 salidas), ST018 Villa Crespo (601) y ST002 San Telmo (556). Solo 3 estaciones tuvieron lluvia en esa franja. | Stock actual por estación y pronóstico: se usa el histórico. Se sabe dónde reponer, no cuántos scooters. |
| 2 | ¿Qué vehículo hay que retirar hoy? | Cassandra (última lectura) + SOH de vehiculos.csv | 16 vehículos con SOH < 70; los más urgentes: V0033 (62,2), V0060 (62,3) y V0043 (62,9). | Las lecturas de Cassandra son del 1/5/2026 (se cargaron 6.000): la lista sale del SOH, no confirma el estado de hoy. |
| 3 | ¿Qué pase venderle a un rider? | Neo4j (intereses) + Mongo (aggregation) | Para R0100: SKU003 Pase 3, el más comprado (41) por los 40 riders con sus mismos intereses. El más vendido en general es SKU004 (117). | Los intereses del grafo y los tags de los pases no tienen mapeo: se recomienda por afinidad entre riders, no por tema. |
| 4 | ¿Hay colusión / fraude social? | Neo4j | Tríos con 10 a 12 viajes juntos desde la misma estación, p. ej. ST005 (R0081, R0077, R0085) y ST017 (R0010, R0114, R0055). R0010 y R0055 aparecen en dos tríos. | VIAJO_CON no guarda hora: no se verifica "menos de 2 min". Es un indicio, no una prueba. |
| 5 | ¿Cuánto se facturó vs. tickets de soporte "cobro"? | Spark (Gold) + Mongo + WordCount en HDFS | Viajes: $345.297.396 (979.760 viajes, 28/2 al 29/5). Ventas: $27.456.400. Tickets #cobro: 294 de 107 riders; 901 pases vendidos (cerca de 1 ticket cada 3 pases). | Los tickets no traen fecha ni monto: no se calcula cuánto se cobró doble. Los períodos de viajes y ventas no coinciden. |

## Qué motores intervienen

Spark/HDFS (P1, P5), Cassandra (P2), MongoDB (P3, P5), Neo4j (P3, P4) y Hadoop WordCount (P5): 5 motores.