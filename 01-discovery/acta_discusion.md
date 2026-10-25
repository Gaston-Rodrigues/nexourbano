# Acta de discusión del squad · ¿Qué V es la más cara de mentir en NexoUrbano?

> Squad de 1 integrante: la discusión fue evaluar las cuatro V (volumen, velocidad, variedad, veracidad) contra los datos medidos en el perfilado.
> La evidencia numérica sale de `evidence/m1_perfilado_viajes.txt` (1.000.000 de viajes, seed 131).

1. Candidatas: las cuatro V. Volumen (poco: 3,7 GB/año de viajes), Velocidad (sólo importa en flota), Variedad y Veracidad.
2. Variedad (viajes en CSV, catálogo en JSON anidado y relaciones en grafo) no es la más cara de mentir: se resuelve eligiendo el motor que modela cada formato (Hive, MongoDB, Neo4j).
3. Elegimos **Veracidad**: un dato falso se propaga a Gold y se convierte en una decisión equivocada.
4. Evidencia propia: 1,34 % de los viajes dura menos de 30 s y 0,68 % más de 4 h.
5. Más grave: el 44,73 % de los viajes tiene velocidad media > 60 km/h, o sea `km` y `duration_s` no son coherentes entre sí.
6. Si rechazáramos esos viajes perderíamos casi la mitad del dataset; por eso la regla R6 **avisa, no rechaza**.
7. Consecuencia de negocio: ingresos y km por día quedarían sobreestimados si usamos `km` sin mirar la duración.
8. En flota el riesgo es mayor: batería o temperatura falsas ocultan una celda defectuosa (seguridad).
9. Control 1: contrato Bronze con reglas R1–R6, verificadas por `tools/validar_contratos.py`.
10. Control 2: en Spark, cada regla cuenta sus rechazados y la suma Silver + cuarentena debe igualar Bronze.
11. Control 3: los rechazados no se pierden. Bronze queda intacto y los viajes que fallan alguna regla se separan en una cuarentena (equivalente a una DLQ), que el job cuenta por regla: 20.240 viajes, 20.184 por R1 y 56 por R2.
12. Control 4: en streaming, rango de batería 0–100 % y watermark de 1 min.
13. Control 5: la facturación de Gold se contrasta con los tickets de "cobro".
14. Qué no resuelve: un GPS alterado dentro del rango válido; lo vamos a mirar con velocidad máxima plausible.
15. Responsable de mantener los contratos: Gastón Rodrigues.