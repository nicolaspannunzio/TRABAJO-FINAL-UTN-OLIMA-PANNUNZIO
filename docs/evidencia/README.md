# Evidencia del recorrido

Recorrido ejecutado sobre el sistema desplegado (Vercel + Render + Supabase) con la semilla de la demo.
Cada paso cita su HU.

| Paso | HU | Qué se muestra | Captura | Resultado |
|---|---|---|---|---|
| 5 | HU-07 | Período abierto con los conceptos activos en `pendiente` | [paso-05](paso-05-abrir-periodo.png) | Ok |
| 6 | HU-08 | Carga de importes, incluidos uno negativo y uno de $0 | [paso-06](paso-06-carga-importes.png) | Ok |
| 7 | HU-08 | Rechazo de duplicado (409, se conserva el primero) | [paso-07](paso-07-importe-original.png) <br> [paso-07.1](paso-07-duplicado-409.png) | Ok (el aviso en pantalla dura un instante, ver issue) |
| 8 | HU-09 | Concepto en no corresponde, distinto del $0 | [paso-08](paso-08-no-corresponde.png) | Ok |
| 9 | HU-10 | Advertencias de variación y sin referencia | [paso-09](paso-09-advertencias.png) | Ok |
| 10 | HU-11 | Bloqueo por pendiente y confirmación | [paso-10](paso-10-bloqueo-pendiente.png) <br> [paso-10.1](paso-10-bloqueo-pendiente-preliquidacion-generada)| Ok |
| 11 | HU-11 | Generación con total y reparto | [paso-11](paso-11-version-2.png) | Ok |
| 12 | HU-12 | Detalle, advertencias y reparto de una versión | [paso-12](paso-12-consulta-versiones-1.png) <br>[paso-12.1](paso-12-consulta-versiones-2.png) | Ok |
| 13 | HU-13, HU-14 | Corrección de un importe y nueva versión | [paso-13](paso-13-correccion-version-3.png) <br>[paso-13.1](paso-13.1-correccion-version-3.png) | Ok |
| 14 | HU-12, HU-14 | Vigente y versiones anteriores intactas | [paso-14](paso-14-vigente-y-anteriores.png) | Ok |