# decision_ops.py - M14: una sola historia de decisión con varios motores
# Se corre desde C:\nexourbano con:  py -X utf8 09-producto\decision_ops.py
import csv
import json
import subprocess
from datetime import datetime, timezone, timedelta 
import re
import sys

UMBRAL_SOH = 70.0   # supuesto nuestro: el TP no define el umbral


def correr(comando, entrada=None):
    # Ejecuta un comando y devuelve toda su salida como texto
    r = subprocess.run(comando, input=entrada, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.stdout + r.stderr

def p1():
    print("=== P1. ¿Dónde reponer scooters en las próximas 3 h si llueve? ===")
    # Hora actual de Buenos Aires (UTC-3)
    hora = datetime.now(timezone(timedelta(hours=-3))).hour
    salida = correr(["docker", "exec", "-e", "HADOOP_USER_NAME=hadoop", "nexo-spark",
                     "/opt/spark/bin/spark-submit", "--master", "local[*]",
                     "/opt/nexo/09-producto/p1_reponer.py", str(hora)])
    for linea in salida.splitlines():
        if linea.startswith(">> P1"):
            print(linea)


def p2():
    print("=== P2. ¿Qué vehículo hay que retirar hoy? (SOH < %s) ===" % UMBRAL_SOH)
    # Candidatos: vehículos con SOH bajo el umbral (el SOH está en vehiculos.csv)
    with open("data/vehiculos.csv", encoding="utf-8") as f:
        candidatos = [v for v in csv.DictReader(f)
                      if float(v["soh_bateria"]) < UMBRAL_SOH]
    print(">> P2 candidatos con SOH bajo el umbral:", len(candidatos))

    # Cassandra: última lectura de cada candidato (ts DESC + LIMIT 1)
    consultas = "".join(
        "SELECT JSON vehicle_id, ts, battery_pct, status FROM nexo.lecturas_vehiculo "
        "WHERE vehicle_id='%s' LIMIT 1; " % v["vehicle_id"] for v in candidatos)
    salida = correr(["docker", "exec", "nexo-cassandra", "cqlsh", "-e", consultas])

    ultimas = {}
    for linea in salida.splitlines():
        linea = linea.strip()
        if linea.startswith("{"):
            d = json.loads(linea)
            ultimas[d["vehicle_id"]] = d

    for v in sorted(candidatos, key=lambda x: float(x["soh_bateria"])):
        u = ultimas.get(v["vehicle_id"])
        if u:
            print(">> P2", v["vehicle_id"], "SOH:", v["soh_bateria"],
                  "| última lectura:", u["ts"], "| batería:", u["battery_pct"],
                  "| estado:", u["status"])
        else:
            print(">> P2", v["vehicle_id"], "SOH:", v["soh_bateria"],
                  "| SIN lecturas en Cassandra (dato faltante)")

RIDER_OBJETIVO = "R0100"


def p3():
    print("=== P3. ¿Qué pase venderle al rider %s? ===" % RIDER_OBJETIVO)

    # Neo4j: riders que comparten al menos un interés con el rider objetivo
    consulta = ("MATCH (r:Rider {rider_id: '%s'})-[:LE_GUSTA]->(i:Interes)"
                "<-[:LE_GUSTA]-(o:Rider) WHERE o <> r "
                "RETURN DISTINCT o.rider_id AS rider_id;" % RIDER_OBJETIVO)
    salida = correr(["docker", "exec", "-i", "nexo-neo4j", "bash", "-c",
                     'cypher-shell -u "${NEO4J_AUTH%%/*}" -p "${NEO4J_AUTH#*/}" --format plain'],
                    entrada=consulta)
    ids = sorted(set(re.findall(r"R\d{4}", salida)))
    print(">> P3 riders que comparten intereses con", RIDER_OBJETIVO, ":", len(ids))

    # Mongo: pase que más compraron esos riders, y pase más vendido en general
    js = """
    const ids = IDS;
    const unir = [
      { $lookup: { from: "productos", localField: "_id", foreignField: "sku", as: "p" } },
      { $unwind: "$p" },
      { $project: { _id: 0, sku: "$_id", nombre: "$p.nombre", tags: "$p.tags", compras: 1 } }
    ];
    const agrupar = [
      { $group: { _id: "$sku", compras: { $sum: 1 } } },
      { $sort: { compras: -1, _id: 1 } },
      { $limit: 1 }
    ];
    const afines = db.ventas.aggregate(
      [{ $match: { categoria: "pase", rider_id: { $in: ids } } }].concat(agrupar, unir)).toArray();
    const general = db.ventas.aggregate(
      [{ $match: { categoria: "pase" } }].concat(agrupar, unir)).toArray();
    print(JSON.stringify({ afines: afines, general: general }));
    """.replace("IDS", json.dumps(ids))
    salida = correr(["docker", "exec", "nexo-mongo", "mongosh", "--quiet", "nexo", "--eval", js])
    resultado = None
    for linea in salida.splitlines():
        if linea.startswith("{"):
            resultado = json.loads(linea)

    if resultado and resultado["afines"]:
        a = resultado["afines"][0]
        print(">> P3 pase más comprado por esos riders:", a["sku"], a["nombre"],
              a["tags"], "compras:", a["compras"])
        g = resultado["general"][0]
        print(">> P3 pase más vendido en general:", g["sku"], g["nombre"],
              g["tags"], "compras:", g["compras"])
    else:
        print(">> P3 FALTA DATO: no se pudo calcular (salida de Mongo):", salida[:300])
    print(">> P3 LIMITE: los intereses del grafo y los tags de los pases no tienen mapeo en los datos")
    
def p4():
    print("=== P4. ¿Hay colusión / fraude social? ===")
    # Se reusa la consulta 4 de M13 (08-neo4j/queries.cypher)
    with open("08-neo4j/queries.cypher", encoding="utf-8") as f:
        texto = f.read()
    consulta = "//" + texto.split("// 4.")[1]
    salida = correr(["docker", "exec", "-i", "nexo-neo4j", "bash", "-c",
                     'cypher-shell -u "${NEO4J_AUTH%%/*}" -p "${NEO4J_AUTH#*/}" --format plain'],
                    entrada=consulta)
    filas = [l for l in salida.splitlines() if l.strip()]
    print(">> P4 filas devueltas (incluye encabezado):", len(filas))
    for l in filas[:6]:
        print(">> P4", l)
    print(">> P4 LIMITE: VIAJO_CON no guarda hora; no se puede verificar '<2 min'. "
          "Es un indicio de colusión, no una prueba")
def p5():
    print("=== P5. ¿Cuánto se facturó vs. tickets de soporte 'cobro'? ===")

    # 1) Spark: facturación por viajes (Gold)
    salida = correr(["docker", "exec", "-e", "HADOOP_USER_NAME=hadoop", "nexo-spark",
                     "/opt/spark/bin/spark-submit", "--master", "local[*]",
                     "/opt/nexo/09-producto/p5_facturacion.py"])
    for linea in salida.splitlines():
        if linea.startswith(">> P5"):
            print(linea)

    # 2) HDFS: conteo de #cobro que dejó el WordCount
    salida = correr(["docker", "exec", "nexo-namenode", "hdfs", "dfs", "-cat",
                     "/nexo/gold/wordcount/part-r-00000"])
    tickets = 0
    for linea in salida.splitlines():
        if linea.startswith("#cobro"):
            tickets = int(linea.split()[-1])
    print(">> P5 tickets #cobro (WordCount en HDFS):", tickets)

    # 3) Riders mencionados en los tickets de cobro
    with open("data/texto_ops.txt", encoding="utf-8") as f:
        ids = sorted({m for l in f if "#cobro" in l
                      for m in re.findall(r"rider (R\d{4})", l)})
    print(">> P5 riders distintos con ticket de cobro:", len(ids))

    # 4) Mongo: ventas totales y pases comprados por esos riders
    js = """
    const ids = IDS;
    const porCategoria = db.ventas.aggregate([
      { $group: { _id: "$categoria", ventas: { $sum: 1 }, total: { $sum: "$monto_ars" } } }
    ]).toArray();
    const delTicket = db.ventas.aggregate([
      { $match: { categoria: "pase", rider_id: { $in: ids } } },
      { $group: { _id: "$rider_id", compras: { $sum: 1 }, total: { $sum: "$monto_ars" } } }
    ]).toArray();
    print(JSON.stringify({ porCategoria: porCategoria, ridersConPase: delTicket.length }));
    """.replace("IDS", json.dumps(ids))
    salida = correr(["docker", "exec", "nexo-mongo", "mongosh", "--quiet", "nexo", "--eval", js])
    datos = None
    for linea in salida.splitlines():
        if linea.startswith("{"):
            datos = json.loads(linea)
    if datos:
        total_ventas = sum(c["total"] for c in datos["porCategoria"])
        pases = [c["ventas"] for c in datos["porCategoria"] if c["_id"] == "pase"]
        print(">> P5 facturado por ventas (Mongo), todas las categorías:", total_ventas)
        print(">> P5 pases vendidos:", pases[0] if pases else 0,
              "| riders con ticket que SÍ compraron pase:", datos["ridersConPase"],
              "de", len(ids))
    else:
        print(">> P5 FALTA DATO: Mongo no devolvió resultado:", salida[:300])
    print(">> P5 LIMITE: los tickets no traen fecha ni monto; no se puede decir cuánto "
          "dinero se cobró doble ni en qué período")

if __name__ == "__main__":
    funciones = {"p1": p1, "p2": p2, "p3": p3, "p4": p4, "p5": p5}
    pedidas = sys.argv[1:] or ["p1", "p2", "p3", "p4", "p5"]
    for nombre in pedidas:
        funciones[nombre]()