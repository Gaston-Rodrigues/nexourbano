// cargar_ventas.js - M11: carga data/ventas.csv en la colección ventas
// Se corre con: docker exec nexo-mongo mongosh --quiet /work/06-mongodb/cargar_ventas.js
const fs = require("fs");
db = db.getSiblingDB("nexo");

// Empezamos de cero para poder repetir el script
db.ventas.drop();

// Leer el CSV: la primera línea son los nombres de las columnas
const lineas = fs.readFileSync("/datos/ventas.csv", "utf8").trim().split("\n");
const columnas = lineas[0].trim().split(",");

const ventas = [];
for (let i = 1; i < lineas.length; i++) {
  const valores = lineas[i].trim().split(",");
  const fila = {};
  for (let j = 0; j < columnas.length; j++) {
    fila[columnas[j]] = valores[j];
  }
  fila.ts = new Date(fila.ts);               // el texto pasa a fecha
  fila.monto_ars = Number(fila.monto_ars);   // el texto pasa a número
  ventas.push(fila);
}

db.ventas.insertMany(ventas);
print(">> ventas cargadas:", db.ventas.countDocuments());
print(">> ejemplo de documento:");
printjson(db.ventas.findOne({}, { _id: 0 }));
print(">> primera fecha:", db.ventas.find().sort({ ts: 1 }).limit(1).toArray()[0].ts.toISOString());
print(">> última fecha:", db.ventas.find().sort({ ts: -1 }).limit(1).toArray()[0].ts.toISOString());