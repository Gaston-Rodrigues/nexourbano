// crud.js - M10: catálogo de productos en MongoDB (CRUD + índice con explain)
// Se corre con: docker exec nexo-mongo mongosh --quiet /work/06-mongodb/crud.js
const fs = require("fs");
db = db.getSiblingDB("nexo");

// Empezamos de cero para poder repetir el script
db.productos.drop();

// ===== C: CREATE (insertMany con los 40 productos del catálogo) =====
const productos = JSON.parse(fs.readFileSync("/datos/productos.json", "utf8"));
db.productos.insertMany(productos);
print(">> CREATE: insertMany -> documentos en la colección: " + db.productos.countDocuments());

// ===== R: READ (find con filtro) =====
print(">> READ: pases activos con el tag 'pro' (sku, nombre y precio en Buenos Aires)");
printjson(db.productos.find(
  { categoria: "pase", tags: "pro", activo: true },
  { _id: 0, sku: 1, nombre: 1, "precios.Buenos Aires": 1 }
).toArray());

// ===== U: UPDATE (updateOne: cambiar el precio de un producto en una ciudad) =====
const antes = db.productos.findOne({ sku: "SKU001" }).precios;
const u = db.productos.updateOne({ sku: "SKU001" }, { $set: { "precios.Buenos Aires": 3990 } });
print(">> UPDATE: SKU001 documentos modificados = " + u.modifiedCount);
print("   precios antes:  " + JSON.stringify(antes));
print("   precios después: " + JSON.stringify(db.productos.findOne({ sku: "SKU001" }).precios));

// ===== D: DELETE (deleteOne de un SKU descontinuado) =====
// Descontinuado = activo: false
let descontinuado = db.productos.findOne({ activo: false });
if (descontinuado === null) {
  // El catálogo no trae ninguno descontinuado: marcamos el último SKU como descontinuado
  descontinuado = db.productos.find().sort({ sku: -1 }).limit(1).toArray()[0];
  db.productos.updateOne({ sku: descontinuado.sku }, { $set: { activo: false } });
}
const d = db.productos.deleteOne({ sku: descontinuado.sku });
print(">> DELETE: se borró " + descontinuado.sku + " (descontinuado), documentos borrados = " + d.deletedCount);
print("   documentos que quedan: " + db.productos.countDocuments());

// ===== ÍNDICE: explain("executionStats") antes y después =====
// Recorre el plan de consulta y devuelve las etapas, por ejemplo "FETCH > IXSCAN"
function etapas(plan) {
  const nombres = [];
  let p = plan.queryPlan ? plan.queryPlan : plan;
  while (p) {
    nombres.push(p.stage);
    p = p.inputStage;
  }
  return nombres.join(" > ");
}

// Mide la consulta "productos con el tag lluvia"
function medir(titulo) {
  const e = db.productos.find({ tags: "lluvia" }).explain("executionStats");
  const s = e.executionStats;
  print(">> " + titulo);
  print("   etapas:", etapas(e.queryPlanner.winningPlan));
  print("   documentos devueltos (nReturned):", s.nReturned);
  print("   claves de índice revisadas (totalKeysExamined):", s.totalKeysExamined);
  print("   documentos revisados (totalDocsExamined):", s.totalDocsExamined);
  print("   tiempo (executionTimeMillis):", s.executionTimeMillis, "ms");
}

medir("ANTES del índice (sin índice en tags)");
db.productos.createIndex({ tags: 1 });
print(">> Índice creado: { tags: 1 }");
medir("DESPUÉS del índice (índice en tags)");