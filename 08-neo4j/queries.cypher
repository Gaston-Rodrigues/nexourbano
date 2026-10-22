// queries.cypher - M13: consultas sobre el grafo de NexoUrbano

// 1. Amigos en común entre R0014 y R0032 (AMIGO_DE se consulta sin dirección)
MATCH (a:Rider {rider_id: 'R0014'})-[:AMIGO_DE]-(c:Rider)-[:AMIGO_DE]-(b:Rider {rider_id: 'R0032'})
RETURN c.rider_id AS amigo_en_comun, c.nombre AS nombre;

// 2. Camino más corto entre R0000 y R0100, siguiendo amistades (hasta 10 saltos)
MATCH camino = shortestPath((a:Rider {rider_id: 'R0000'})-[:AMIGO_DE*..10]-(b:Rider {rider_id: 'R0100'}))
RETURN [n IN nodes(camino) | n.rider_id] AS camino, length(camino) AS saltos;

// 3. Recomendación: riders que salen de las mismas estaciones que R0100 y no son sus amigos
MATCH (a:Rider {rider_id: 'R0100'})-[:SALE_DE]->(e:Estacion)<-[:SALE_DE]-(b:Rider)
WHERE a <> b AND NOT (a)-[:AMIGO_DE]-(b)
RETURN b.rider_id AS recomendado, collect(e.station_id) AS estaciones_en_comun, count(e) AS cantidad
ORDER BY cantidad DESC, recomendado
LIMIT 5;

// 4. (Extra) Patrón sospechoso: 3 riders encadenados por VIAJO_CON desde la misma estación.
// Límite: el grafo no tiene la hora de cada viaje, así que no se puede comprobar "en menos de 2 minutos".
MATCH (a:Rider)-[x:VIAJO_CON]-(b:Rider)-[y:VIAJO_CON]-(c:Rider)
WHERE a.rider_id < c.rider_id AND x.station_id = y.station_id
RETURN x.station_id AS estacion, a.rider_id AS rider_1, b.rider_id AS rider_2, c.rider_id AS rider_3,
       x.n + y.n AS viajes_juntos
ORDER BY viajes_juntos DESC
LIMIT 5; 