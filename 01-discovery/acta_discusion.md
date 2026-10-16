# Acta de discusión del squad · ¿Qué V es la más cara de mentir en NexoUrbano?

> Squad de 1 integrante: la discusión fue evaluar las tres candidatas (volumen, velocidad, veracidad) contra los datos medidos en el perfilado.
> La evidencia numérica sale de `evidence/m1_perfilado_viajes.txt` (1.000.000 de viajes, seed 131).

1. Candidatas: Volumen (poco: 3,7 GB/año de viajes), Velocidad (sólo importa en flota) y Veracidad.
2. Elegimos **Veracidad**: un dato falso se propaga a Gold y se convierte en una decisión equivocada.
3. Evidencia propia: 1,34 % de los viajes dura menos de 30 s y 0,68 % más de 4 h.
4. Más grave: el 44,73 % de los viajes tiene velocidad media > 60 km/h, o sea `km` y `duration_s` no son coherentes entre sí.
5. Si rechazáramos esos viajes perderíamos casi la mitad del dataset; por eso la regla R6 **avisa, no rechaza**.
6. Consecuencia de negocio: ingresos y km por día quedarían sobreestimados si usamos `km` sin mirar la duración.
7. En flota el riesgo es mayor: batería o temperatura falsas ocultan una celda defectuosa (seguridad).
8. Control 1: contrato Bronze con reglas R1–R6, verificadas por `tools/validar_contratos.py`.
9. Control 2: en Spark, cada regla cuenta sus rechazados y la suma Silver + cuarentena debe igualar Bronze.
10. Control 3: los rechazados no se borran: van a `bronze/_cuarentena/` con la regla violada.
11. Control 4: en streaming, rango de batería 0–100 % y watermark de 1 min.
12. Control 5: la facturación de Gold se contrasta con los tickets de "cobro".
13. Qué no resuelve: un GPS alterado dentro del rango válido; lo vamos a mirar con velocidad máxima plausible.
14. Qué falta decidir: umbral de velocidad para el streaming (¿25, 40 o 60 km/h?).
15. Responsable de mantener los contratos: Gastón Rodrigues.