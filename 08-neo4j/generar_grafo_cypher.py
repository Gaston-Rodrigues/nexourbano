# generar_grafo_cypher.py - M13: arma 08-neo4j/grafo.cypher con los datos del proyecto
# Se corre desde la raíz del proyecto: python 08-neo4j\generar_grafo_cypher.py
import csv
import json


def comillas(valor):
    # Cypher usa comillas simples: escapamos las que pueda traer el texto
    return "'" + str(valor).replace("\\", "\\\\").replace("'", "\\'") + "'"


# 1. Leer los datos
with open("data/riders.csv", newline="", encoding="utf-8") as f:
    riders = list(csv.DictReader(f))
with open("data/estaciones.csv", newline="", encoding="utf-8") as f:
    estaciones = list(csv.DictReader(f))
with open("data/grafo.json", encoding="utf-8") as f:
    grafo = json.load(f)

lineas = []

# 2. Encabezado y reglas de unicidad
lineas.append("// grafo.cypher - M13: grafo social de NexoUrbano (generado por generar_grafo_cypher.py)")
lineas.append("// Nodos: Rider, Interes, Estacion")
lineas.append("// Relaciones: AMIGO_DE, VIAJO_CON, LE_GUSTA, SALE_DE")
lineas.append("// AMIGO_DE se guarda en una dirección, pero se consulta sin dirección (es simétrica).")
lineas.append("// SALE_DE se deduce de viajo_con: si dos riders viajaron juntos desde una estación,")
lineas.append("// cada uno sale de esa estación (viajes = suma de los viajes en común desde ahí).")
lineas.append("")
lineas.append("// Empezar de cero para poder repetir el script")
lineas.append("MATCH (n) DETACH DELETE n;")
lineas.append("CREATE CONSTRAINT rider_id IF NOT EXISTS FOR (r:Rider) REQUIRE r.rider_id IS UNIQUE;")
lineas.append("CREATE CONSTRAINT estacion_id IF NOT EXISTS FOR (e:Estacion) REQUIRE e.station_id IS UNIQUE;")
lineas.append("CREATE CONSTRAINT interes_nombre IF NOT EXISTS FOR (i:Interes) REQUIRE i.nombre IS UNIQUE;")
lineas.append("")

# 3. Nodos
for r in riders:
    lineas.append("CREATE (:Rider {rider_id: %s, nombre: %s, plan: %s, ciudad: %s});"
                  % (comillas(r["rider_id"]), comillas(r["nombre"]), comillas(r["plan"]), comillas(r["ciudad"])))

for e in estaciones:
    lineas.append("CREATE (:Estacion {station_id: %s, nombre: %s, barrio: %s, lat: %s, lon: %s});"
                  % (comillas(e["station_id"]), comillas(e["nombre"]), comillas(e["barrio"]), e["lat"], e["lon"]))

for interes in sorted(set(g["interes"] for g in grafo["le_gusta"])):
    lineas.append("CREATE (:Interes {nombre: %s});" % comillas(interes))
lineas.append("")

# 4. Relaciones
for a in grafo["amigos"]:
    lineas.append("MATCH (a:Rider {rider_id: %s}), (b:Rider {rider_id: %s}) CREATE (a)-[:AMIGO_DE]->(b);"
                  % (comillas(a["a"]), comillas(a["b"])))

for v in grafo["viajo_con"]:
    lineas.append("MATCH (a:Rider {rider_id: %s}), (b:Rider {rider_id: %s}) "
                  "CREATE (a)-[:VIAJO_CON {station_id: %s, n: %d}]->(b);"
                  % (comillas(v["a"]), comillas(v["b"]), comillas(v["station_id"]), v["n"]))

for g in grafo["le_gusta"]:
    lineas.append("MATCH (r:Rider {rider_id: %s}), (i:Interes {nombre: %s}) CREATE (r)-[:LE_GUSTA]->(i);"
                  % (comillas(g["rider_id"]), comillas(g["interes"])))

# SALE_DE: cada rider de un viajo_con sale de esa estación (se suman los viajes)
salidas = {}
for v in grafo["viajo_con"]:
    for rider in (v["a"], v["b"]):
        clave = (rider, v["station_id"])
        salidas[clave] = salidas.get(clave, 0) + v["n"]

for (rider, estacion), viajes in sorted(salidas.items()):
    lineas.append("MATCH (r:Rider {rider_id: %s}), (e:Estacion {station_id: %s}) "
                  "CREATE (r)-[:SALE_DE {viajes: %d}]->(e);"
                  % (comillas(rider), comillas(estacion), viajes))
lineas.append("")

# 5. Comprobación: cuántos nodos y relaciones quedaron
lineas.append("MATCH (n) RETURN labels(n)[0] AS nodo, count(*) AS cantidad ORDER BY nodo;")
lineas.append("MATCH ()-[r]->() RETURN type(r) AS relacion, count(*) AS cantidad ORDER BY relacion;")

with open("08-neo4j/grafo.cypher", "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lineas) + "\n")

print("grafo.cypher generado con", len(lineas), "líneas")
print("Riders:", len(riders), "| Estaciones:", len(estaciones), "| SALE_DE:", len(salidas))  