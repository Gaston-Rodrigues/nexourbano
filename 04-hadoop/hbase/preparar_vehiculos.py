# Prepara los comandos de HBase para cargar los vehiculos.
# Lee vehiculos.csv y calcula el ultimo GPS de cada vehiculo
# con el punto final de su ultimo viaje en viajes.csv.
import csv

# 1. Buscar el ultimo viaje de cada vehiculo
ultimo_viaje = {}  # vehicle_id -> (ts_end, lat_end, lon_end)
with open("data/viajes.csv", newline="", encoding="utf-8") as f:
    for fila in csv.DictReader(f):
        vid = fila["vehicle_id"]
        ts = fila["ts_end"]
        if vid not in ultimo_viaje or ts > ultimo_viaje[vid][0]:
            ultimo_viaje[vid] = (ts, fila["lat_end"], fila["lon_end"])

# 2. Armar los comandos de HBase
comandos = []
comandos.append("create_namespace 'nexo'")
comandos.append("create 'nexo:vehiculos', 'id', 'telemetry'")

sin_gps = 0
with open("data/vehiculos.csv", newline="", encoding="utf-8") as f:
    for fila in csv.DictReader(f):
        vid = fila["vehicle_id"]
        numero = int(vid[1:])
        rowkey = f"{numero % 4}_{vid}"  # prefijo 0-3 para repartir las claves

        if vid in ultimo_viaje:
            gps = f"{ultimo_viaje[vid][1]},{ultimo_viaje[vid][2]}"
        else:
            gps = "sin_dato"
            sin_gps += 1

        comandos.append(f"put 'nexo:vehiculos', '{rowkey}', 'id:vehicle_id', '{vid}'")
        comandos.append(f"put 'nexo:vehiculos', '{rowkey}', 'id:modelo', '{fila['modelo']}'")
        comandos.append(f"put 'nexo:vehiculos', '{rowkey}', 'telemetry:soh_bateria', '{fila['soh_bateria']}'")
        comandos.append(f"put 'nexo:vehiculos', '{rowkey}', 'telemetry:ultimo_gps', '{gps}'")
        comandos.append(f"put 'nexo:vehiculos', '{rowkey}', 'telemetry:estado', '{fila['estado']}'")

comandos.append("exit")

# 3. Guardar el archivo
with open("04-hadoop/hbase/cargar_vehiculos.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(comandos) + "\n")

print("Vehiculos procesados:", len(ultimo_viaje), "con viajes en viajes.csv")
print("Vehiculos sin viajes (gps = sin_dato):", sin_gps)
print("Comandos escritos:", len(comandos))