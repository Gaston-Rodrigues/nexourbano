-- queries.cql - M12: consultas sobre lecturas_vehiculo
USE nexo;

-- 1. Últimas 20 lecturas de un vehículo (ts DESC: primero las más nuevas)
SELECT vehicle_id, ts, battery_pct, temp_c, status
FROM lecturas_vehiculo
WHERE vehicle_id = 'V0030'
LIMIT 20;

-- 2. Rango horario de un vehículo: lecturas entre las 06:00 y las 10:00 UTC
SELECT vehicle_id, ts, battery_pct, temp_c, status
FROM lecturas_vehiculo
WHERE vehicle_id = 'V0030'
  AND ts >= '2026-05-01 06:00:00+0000'
  AND ts <  '2026-05-01 10:00:00+0000';

-- 3. ERROR A PROPÓSITO: filtrar por una columna que no es la partition key.
-- La tabla está hecha para consultar por vehículo; buscar por status obligaría
-- a recorrer todos los vehículos, y Cassandra lo rechaza.
SELECT * FROM lecturas_vehiculo WHERE status = 'battery_low'; 