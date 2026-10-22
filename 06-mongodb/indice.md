# Índice en tags: explain("executionStats") antes y después

Consulta: `db.productos.find({ tags: "lluvia" })` sobre 39 productos (después del `deleteOne`). Evidencia: `evidence/mongodb/crud.log`.

| | Sin índice | Con índice `{ tags: 1 }` |
|---|---|---|
| Etapas | COLLSCAN | FETCH > IXSCAN |
| Documentos devueltos | 15 | 15 |
| Claves de índice revisadas | 0 | 15 |
| Documentos revisados | 39 | 15 |
| Tiempo (`executionTimeMillis`) | 0 ms | 2 ms |

**Lectura honesta:** con 39 documentos el tiempo no sirve para comparar (0 y 2 ms es ruido de medición; el índice no salió más rápido). Lo que sí cambia es el trabajo: de revisar los 39 documentos a revisar solo los 15 que coinciden. Con millones de productos esa diferencia sí se vería en el tiempo. El índice es *multikey* porque `tags` es una lista: tiene una entrada por cada tag. 