# Comparativa: SQL contra documento

1. **Consulta:** la ficha completa de un producto (SKU001): nombre, categoría, tags, y precio y stock por ciudad.
2. **En SQL** (modelo normalizado, tablas hipotéticas `productos`, `producto_tags`, `precios` y `stock`) hacen falta 3 joins:
```sql
   SELECT p.nombre, p.categoria, t.tag, pr.ciudad, pr.precio, s.stock
   FROM productos p
   JOIN producto_tags t ON t.sku = p.sku
   JOIN precios pr ON pr.sku = p.sku
   JOIN stock s ON s.sku = p.sku AND s.ciudad = pr.ciudad
   WHERE p.sku = 'SKU001';
```
3. **Problema en SQL:** el resultado multiplica filas (2 tags × 2 ciudades = 4 filas con datos repetidos) y la aplicación tiene que volver a agruparlas.
4. **En Mongo** es una sola lectura, sin joins: `db.productos.findOne({ sku: "SKU001" })` devuelve un documento con tags, precios y stock anidados.
5. **Por qué funciona:** lo que se lee junto se guarda junto, así que una consulta por SKU es una sola búsqueda.
6. **Lo que se paga:** el modelo documento duplica datos (renombrar un tag obliga a un `updateMany` sobre todos los productos) y no tiene claves foráneas que impidan inconsistencias.
7. **Cuándo gana SQL:** cuando hay que cruzar productos con ventas, armar reportes ad hoc con muchos joins o garantizar integridad referencial.
8. **Conclusión:** para el catálogo, que casi siempre se lee entero por SKU, conviene el documento; para ventas y finanzas, conviene SQL. 