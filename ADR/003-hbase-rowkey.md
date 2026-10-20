# ADR 003 — Clave de fila de HBase (nexo:vehiculos)

- **Contexto:** HBase guarda las filas ordenadas por clave. Con claves seguidas (V0000, V0001, V0002...) las escrituras nuevas caen siempre en la misma región y un solo servidor concentra el trabajo (hotspot).
- **Decisión:** la clave es `<resto de numero/4>_<vehicle_id>`, por ejemplo `2_V0042`. El prefijo (0 a 3) reparte los vehículos en 4 grupos.
- **Búsqueda:** el prefijo se recalcula desde el id, así que `get` por vehículo sigue siendo directo y no hace falta recorrer la tabla.
- **Consecuencia:** se pierde el orden natural por id (para listar todos hay que recorrer los 4 prefijos); a cambio las escrituras se reparten entre regiones.
- **Límite:** con 80 vehículos el hotspot no se nota en el sandbox; el diseño apunta a una flota real de miles de vehículos con telemetría constante. 