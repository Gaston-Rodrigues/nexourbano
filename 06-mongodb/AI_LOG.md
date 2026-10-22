# AI_LOG · 06-mongodb

| Fecha | Prompt (resumen) | Qué se aceptó | Qué se corrigió a mano | Qué falló |
| 2026-10-22 | Construimos juntos, con Claude como guía: colección productos en MongoDB, CRUD completo (crud.js), índice en tags con explain antes y después, y comparativa SQL contra documento | crud.js, indice.md, comparativa_sql_vs_documento.md y los montajes de Mongo en docker-compose.yml | Nombres de archivos y textos de los dos documentos | Nada falló en la corrida; el índice no mejoró el tiempo (0 ms contra 2 ms) con solo 39 documentos y quedó documentado así |
| 2026-10-22 | Construimos juntos, con Claude como guía: carga de ventas en MongoDB, pipeline de agregación (match, group, lookup y project) y exportación a ventas_agg.json | cargar_ventas.js, ventas_pipeline.js y 09-producto/ventas_agg.json | Nombres de archivos y la definición de último trimestre (abril a junio de 2026, hora de Buenos Aires) | Nada falló; el extra geoespacial (opcional) no se hizo |
