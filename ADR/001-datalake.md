# ADR 001 · Data lake: MinIO local en lugar de Azure ADLS Gen2

- **Estado:** aceptada
- **Fecha:** 2026-10-15

## Decisión
Usamos MinIO (compatible con S3) en Docker como data lake. Tiene los
buckets `bronze`, `silver` y `gold`. Los datos de Azure ADLS Gen2 se
reemplazan por MinIO porque el TP se hace en local, sin gastar dinero.

## Criterios medibles

| Criterio | MinIO local | Azure ADLS Gen2 (East US, Hot, LRS) |
|---|---|---|
| Costo de guardar 1 TB al mes | USD 0 (usa mi disco) | 1024 GB x USD 0,021 = USD 21,50 |
| Costo de sacar 1 TB (egress) | USD 0 | (1000 GB - 100 GB gratis) x USD 0,087 = USD 78,30 |
| Permisos (IAM) | 1 usuario administrador (root) con clave en `.env`; sin roles por carpeta | Control por roles de Azure (RBAC) sobre cada contenedor, por ejemplo *Storage Blob Data Reader* o *Contributor*, con identidades de Microsoft Entra ID |
| Tiempo hasta el primer byte | **4,1 ms** de mediana (mín. 2,2 ms, máx. 15,6 ms), medido en 10 intentos con `tools/medir_ttfb.py` | No medido: no tenemos cuenta de Azure. Depende de la región y de la red; se medirá con el mismo script al migrar |

Evidencia de la medición: `evidence/azure/04_ttfb_minio.txt`.

Fuentes de precios (consultados el 2026-10-15, región East US, LRS, nivel Hot, USD):
- Almacenamiento: https://azure.microsoft.com/es-es/pricing/details/storage/data-lake/
- Salida de datos: https://azure.microsoft.com/es-es/pricing/details/bandwidth/

## Qué cambia en producción con Azure
- La URI pasa de `s3a://bronze/...` a `abfss://bronze@<cuenta>.dfs.core.windows.net/...`.
- Los permisos se manejan con roles de Azure, no con una clave fija.
- Se paga por almacenamiento, lecturas y salida de datos.
- Los contratos y los scripts casi no cambian: solo la dirección del lake.