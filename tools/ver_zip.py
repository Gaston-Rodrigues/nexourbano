# ver_zip.py - M1: lista lo que hay adentro del zip de Citi Bike (no extrae nada)
# Uso:  py tools\ver_zip.py
import zipfile

ZIP = "data/open/citibike_202609.zip"

with zipfile.ZipFile(ZIP) as z:
    for archivo in z.infolist():
        mb = archivo.file_size / 1_000_000
        print(f"{archivo.filename}  ({mb:,.0f} MB sin comprimir)")