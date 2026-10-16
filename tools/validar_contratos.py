#!/usr/bin/env python3
"""Valida que cada contrato en contratos/ tenga lo que exige el TP:
schema, grano, clave, SLA de frescura y owner. Sale con código 1 si falta algo.
    py tools/validar_contratos.py
"""
import sys
from pathlib import Path

import yaml

REQUERIDOS = ["dataset", "version", "layer", "owner", "grain", "key",
              "sla_freshness", "timezone", "columns", "quality_rules"]
errores = 0
archivos = sorted(Path("contratos").glob("*.yaml"))
for f in archivos:
    c = yaml.safe_load(f.read_text(encoding="utf-8"))
    faltan = [k for k in REQUERIDOS if not c.get(k)]
    cols = {x["name"] for x in c.get("columns", [])}
    clave_ok = all(k in cols for k in c.get("key", [])) or c.get("layer") == "gold"
    if faltan or not clave_ok:
        errores += 1
        print(f"FAIL {f.name}: faltan {faltan}" + ("" if clave_ok else " | clave no está en columns"))
    else:
        print(f"OK   {f.name}  ({c['layer']}, {len(cols)} columnas, {len(c['quality_rules'])} reglas)")
print(f"\n{len(archivos)} contratos, {errores} con errores")
sys.exit(1 if errores else 0)
