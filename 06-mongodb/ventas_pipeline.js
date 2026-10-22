// ventas_pipeline.js - M11: analítica comercial con aggregation pipeline
// Imprime SOLO el JSON final. Se exporta con:
// docker exec nexo-mongo mongosh --quiet /work/06-mongodb/ventas_pipeline.js > 09-producto\ventas_agg.json
db = db.getSiblingDB("nexo");

const ZONA = "America/Argentina/Buenos_Aires";

// 1. $match: último trimestre = segundo trimestre de 2026 (abril a junio, hora de Buenos Aires)
const desde = new Date("2026-04-01T00:00:00-03:00");
const hasta = new Date("2026-07-01T00:00:00-03:00");
const trimestre = { $match: { ts: { $gte: desde, $lt: hasta } } };

// 2. Total por categoría
const porCategoria = db.ventas.aggregate([
  trimestre,
  { $group: { _id: "$categoria", ventas: { $sum: 1 }, total_ars: { $sum: "$monto_ars" } } },
  { $sort: { total_ars: -1 } },
  { $project: { _id: 0, categoria: "$_id", ventas: 1, total_ars: 1 } }
]).toArray();

// 3. Top 5 productos, con $lookup a la colección productos para traer el nombre
const top5 = db.ventas.aggregate([
  trimestre,
  { $group: { _id: "$sku", ventas: { $sum: 1 }, total_ars: { $sum: "$monto_ars" } } },
  { $sort: { total_ars: -1, _id: 1 } },
  { $limit: 5 },
  { $lookup: { from: "productos", localField: "_id", foreignField: "sku", as: "producto" } },
  { $unwind: { path: "$producto", preserveNullAndEmptyArrays: true } },
  { $project: { _id: 0, sku: "$_id", nombre: "$producto.nombre",
                categoria: "$producto.categoria", ventas: 1, total_ars: 1 } }
]).toArray();

// 4. Ventas por mes (el mes se calcula en hora de Buenos Aires)
const porMes = db.ventas.aggregate([
  trimestre,
  { $group: { _id: { $dateToString: { format: "%Y-%m", date: "$ts", timezone: ZONA } },
              ventas: { $sum: 1 }, total_ars: { $sum: "$monto_ars" } } },
  { $sort: { _id: 1 } },
  { $project: { _id: 0, mes: "$_id", ventas: 1, total_ars: 1 } }
]).toArray();

// 5. Documento de salida limpio
const salida = {
  periodo: {
    descripcion: "segundo trimestre de 2026 (hora de Buenos Aires); junio llega hasta el 14/6",
    desde: desde.toISOString(),
    hasta: hasta.toISOString()
  },
  ventas_en_periodo: db.ventas.countDocuments({ ts: { $gte: desde, $lt: hasta } }),
  total_por_categoria: porCategoria,
  top5_productos: top5,
  ventas_por_mes: porMes
};
print(JSON.stringify(salida, null, 2)); 