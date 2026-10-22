-- schema.cql - M12: keyspace y tabla de lecturas de sensores

-- RF = 1 porque en el sandbox hay un solo nodo de Cassandra.
-- En producción el factor de replicación tiene que ser RF >= 3 (con NetworkTopologyStrategy),
-- así los datos se copian en 3 nodos y el cluster sigue funcionando si uno se cae.
CREATE KEYSPACE IF NOT EXISTS nexo
  WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE nexo;

-- Tabla modelada por consulta: lecturas de un vehículo, de la más nueva a la más vieja
CREATE TABLE IF NOT EXISTS lecturas_vehiculo (
  vehicle_id  text,
  ts          timestamp,
  lat         double,
  lon         double,
  battery_pct double,
  temp_c      double,
  status      text,
  PRIMARY KEY ((vehicle_id), ts)
) WITH CLUSTERING ORDER BY (ts DESC);

DESCRIBE TABLE lecturas_vehiculo; 