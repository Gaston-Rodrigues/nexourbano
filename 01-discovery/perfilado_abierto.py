# perfilado_abierto.py - M1: perfilado de un dataset abierto real (Citi Bike NYC)
# Lee solo el primer CSV del zip (~1 millón de viajes). NO modifica nada.
# Uso:  py 01-discovery\perfilado_abierto.py
import os
import zipfile
import pandas as pd

ZIP = "data/open/citibike_202609.zip"
CSV = "202609-citibike-tripdata_1.csv"                  # una de las 5 partes del mes
SALIDA = "evidence/m1_perfilado_citibike.txt"           # acá se guarda el reporte

# Cada línea que mostramos en pantalla también se guarda para el reporte
lineas = []
def p(texto=""):
    print(texto)
    lineas.append(str(texto))

# 1. Cargar los datos (leyendo directo del zip)
with zipfile.ZipFile(ZIP) as z:
    with z.open(CSV) as archivo:
        df = pd.read_csv(archivo)
p(f"PERFILADO de {CSV} (Citi Bike NYC, sep 2026): {len(df):,} filas x {df.shape[1]} columnas")

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

# 5. Outliers: la duración sale de restar fin - inicio
inicio = pd.to_datetime(df["started_at"], format="mixed")
fin = pd.to_datetime(df["ended_at"], format="mixed")
df["duration_s"] = (fin - inicio).dt.total_seconds()
p("\n--- 5. Outliers ---")
p("Duración en segundos:")
p(df["duration_s"].describe())
negativos = (df["duration_s"] <= 0).sum()               # termina antes de empezar
cortos = (df["duration_s"] < 30).sum()                  # menos de 30 segundos
largos = (df["duration_s"] > 4 * 3600).sum()            # más de 4 horas
p(f"Viajes con duración <= 0:     {negativos:,}")
p(f"Viajes de menos de 30 segundos: {cortos:,} ({100 * cortos / len(df):.2f}%)")
p(f"Viajes de más de 4 horas:       {largos:,} ({100 * largos / len(df):.2f}%)")

# 6. Drift temporal: cuántos viajes hay por día
p("\n--- 6. Drift temporal ---")
df["dia"] = inicio.dt.strftime("%Y-%m-%d")
por_dia = df.groupby("dia").size()
p(f"Rango de fechas: {df['dia'].min()} a {df['dia'].max()}")
p(f"Viajes por día: mínimo {por_dia.min():,}, máximo {por_dia.max():,}")
p(por_dia.head(10))

# Guardar el reporte como evidencia
os.makedirs("evidence", exist_ok=True)
with open(SALIDA, "w", encoding="utf-8") as f:
    f.write("\n".join(lineas))
print(f"\nReporte guardado en {SALIDA}")