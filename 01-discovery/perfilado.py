# perfilado.py - M1: perfilado del dataset de viajes
# Mira el archivo y cuenta cosas raras. NO borra ni modifica nada.
# Uso:  py 01-discovery\perfilado.py
import os
import pandas as pd

ARCHIVO = "data/viajes.csv"                    # 1 millón de viajes (generador, semilla 131)
SALIDA = "evidence/m1_perfilado_viajes.txt"    # acá se guarda el reporte

# Cada línea que mostramos en pantalla también se guarda para el reporte
lineas = []
def p(texto=""):
    print(texto)
    lineas.append(str(texto))

# 1. Cargar los datos
df = pd.read_csv(ARCHIVO)
p(f"PERFILADO de {ARCHIVO}: {len(df):,} filas x {df.shape[1]} columnas")

# 2. Tipos de dato y nulos
p("\n--- 1. Tipos de dato ---")
p(df.dtypes)
p("\n--- 2. Nulos por columna ---")
p(df.isnull().sum())

# 3. Cardinalidad: cuántos valores distintos tiene cada columna
p("\n--- 3. Cardinalidad ---")
p(df.nunique())

# 4. Duplicados: ride_id tiene que ser único
duplicados = df["ride_id"].duplicated().sum()
p(f"\n--- 4. ride_id duplicados: {duplicados:,} ---")

# 5. Outliers (valores raros)
p("\n--- 5. Outliers ---")
p("Duración en segundos:")
p(df["duration_s"].describe())
cortos = (df["duration_s"] < 30).sum()          # menos de 30 segundos
largos = (df["duration_s"] > 4 * 3600).sum()    # más de 4 horas
sin_km = (df["km"] <= 0).sum()                  # distancia cero o negativa
p(f"Viajes de menos de 30 segundos: {cortos:,} ({100 * cortos / len(df):.2f}%)")
p(f"Viajes de más de 4 horas:       {largos:,} ({100 * largos / len(df):.2f}%)")
p(f"Viajes con distancia <= 0:      {sin_km:,}")

# 6. Velocidad media = km / horas. Si da muy alta, km y duración no cuadran
df["vel_kmh"] = df["km"] / (df["duration_s"] / 3600)
rapidos = (df["vel_kmh"] > 60).sum()
p(f"Viajes con velocidad media > 60 km/h: {rapidos:,} ({100 * rapidos / len(df):.2f}%)")

# 7. Drift temporal: cómo cambian los datos a lo largo del tiempo
p("\n--- 6. Drift temporal ---")
inicio = pd.to_datetime(df["ts_start"])
df["dia"] = inicio.dt.strftime("%Y-%m-%d")
df["mes"] = inicio.dt.strftime("%Y-%m")
por_dia = df.groupby("dia").size()
p(f"Rango de fechas: {df['dia'].min()} a {df['dia'].max()}")
p(f"Viajes por día: mínimo {por_dia.min():,}, máximo {por_dia.max():,}")
p("Últimos 3 días (el último suele venir incompleto):")
p(por_dia.tail(3))
p("Viajes y duración media por mes:")
p(df.groupby("mes")["duration_s"].agg(["count", "mean"]).round(1))

# 8. Resumen: reglas que vamos a aplicar en Silver (ver contratos/bronze_viajes.yaml)
p("\n=== RESUMEN ===")
p(f"Se rechazan en Silver: duración < 30 s ({cortos:,}), duración > 4 h ({largos:,}), distancia <= 0 ({sin_km:,})")
p(f"Solo se avisa (no se rechaza): velocidad > 60 km/h ({rapidos:,})")

# Guardar el reporte como evidencia
os.makedirs("evidence", exist_ok=True)
with open(SALIDA, "w", encoding="utf-8") as f:
    f.write("\n".join(lineas))
print(f"\nReporte guardado en {SALIDA}")