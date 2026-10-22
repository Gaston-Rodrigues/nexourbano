#!/bin/bash
# correr_cypher.sh - ejecuta un archivo .cypher en Neo4j
# Usuario y contraseña: se toman de NEO4J_AUTH, que ya está definida dentro del contenedor (formato usuario/contraseña)
USUARIO="${NEO4J_AUTH%%/*}"
CLAVE="${NEO4J_AUTH#*/}"
cypher-shell -u "$USUARIO" -p "$CLAVE" -f "$1"  