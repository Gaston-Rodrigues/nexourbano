# Bitácora de IA — NexoUrbano

Squad: 131 (Gastón Rodrigues, integrante único)

Herramientas usadas: Claude Sonnet 5.5, de Anthropic

Regla: una fila por sesión relevante. Mentir acá desaprueba el bloque A.

| Fecha | Módulo | Prompt (resumen) | Qué se aceptó | Qué se corrigió a mano | Qué falló |
|---|---|---|---|---|---|
| 15/10/2026 | Base | Levantar el entorno con Docker | Estructura del entorno y explicación de los servicios | Lo construimos juntos, con Claude como guía, y probé cada servicio | Neo4j reiniciaba sin parar. MySQL rechazó la clave por un volumen viejo |
| 15/10/2026 | M1 | Perfilado de datos, reglas de calidad, 4 V y documentos | Propuesta de código y estructura de los documentos | Construimos el código y los documentos juntos, con Claude como guía. Revisé contra el enunciado | La primera versión del código era demasiado compleja. Había cifras sin fuente |
| 16/10/2026 | M2 | ADR 001: data lake con Azure frente a MinIO | Estructura del ADR y fórmulas de costo | Lo construimos juntos, con Claude como guía. Busqué los precios en Azure | Página de precios sin valores en una región. ⚠ Azure no medido: se usó MinIO como plan B |
| 16/10/2026 | M3 | Notebook de Databricks y contrato de la tabla Silver | Estructura del notebook, reglas de calidad y contrato | Construimos el notebook y el contrato juntos, con Claude como guía. Probé cada celda | Bluesky dio 403 y se usó Mastodon. Error 429. ⚠ Posts de Mastodon con ruido |