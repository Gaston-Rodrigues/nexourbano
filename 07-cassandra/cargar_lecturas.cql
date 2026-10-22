-- cargar_lecturas.cql - M12: carga las lecturas de sensores desde el CSV
USE nexo;

COPY lecturas_vehiculo (vehicle_id, ts, lat, lon, battery_pct, temp_c, status)
  FROM '/data/lecturas_sensores.csv'
  WITH HEADER = TRUE AND DATETIMEFORMAT = '%Y-%m-%dT%H:%M:%S%z';

-- Comprobar cuántas filas quedaron
SELECT COUNT(*) FROM lecturas_vehiculo; 