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
## Recorrido del integrante B (Gate 1): pasos 1 a 4 y usuarios

Comprobaciones de las HU del integrante A, hechas por el integrante B sobre el sistema desplegado (Vercel + Render + Supabase) con la semilla de la demo. Las capturas están en [`gate1-b/`](gate1-b/).

| Paso | HU | Qué se muestra | Captura | Resultado |
|---|---|---|---|---|
| — | — | Backend en Render desplegado desde el último commit de `main` (`9924d90`) | [G1-B-00a](gate1-b/G1-B-00a-render-deploy.png) | Ok |
| 1 | HU-01 | Inicio de sesión con la cuenta admin | [G1-B-01](gate1-b/G1-B-01-login-ok-01.png) | Ok |
| 1 | HU-01 | Request sin token al backend: 401 `no_autenticado`, sin datos | [G1-B-02](gate1-b/G1-B-02-sin-token-401.png) | Ok |
| 1 | HU-01 | Cerrar sesión vuelve al login | [G1-B-03](gate1-b/G1-B-03-logout.png) | Ok |
| 1 | HU-01 | Un usuario dado de baja no puede ingresar | [G1-B-19](gate1-b/G1-B-19-inactivo-rechazado.png) | Ok |
| 2 | HU-03 | Propiedad y propietarios de la semilla | [G1-B-04](gate1-b/G1-B-04-propiedad-semilla.png) | Ok |
| 2 | HU-03 | Una propiedad nueva queda en estado `activa` | [G1-B-05](gate1-b/G1-B-05-propiedad-nueva-activa.png) | Ok |
| 2 | HU-03 | Un propietario ya asociado no se ofrece para asociarlo otra vez | [G1-B-06](gate1-b/G1-B-06-no-repite-propietario.png) | Ok |
| 3 | HU-04 | Porcentajes que suman 90: no se puede guardar | [G1-B-07](gate1-b/G1-B-07-suma-90-rechazada.png) | Ok |
| 3 | HU-04 | Porcentaje 0 o mayor que 100: rechazado | [G1-B-08](gate1-b/G1-B-08-porcentaje-0.png) | Ok |
| 3 | HU-04 | Cambio del reparto de 50/50 a 60/40 | [G1-B-09](gate1-b/G1-B-09-reparto-60-40.png) | Ok |
| 3 | HU-04 | Vuelta a 50/50 (base de la demo) | [G1-B-10](gate1-b/G1-B-10-reparto-vuelta-50-50.png) | Ok |
| 4 | HU-05 | Catálogo con un concepto de umbral propio (Expensas, 50 %) | [G1-B-11](gate1-b/G1-B-11-catalogo.png) | Ok |
| 4 | HU-05 | Concepto nuevo sin umbral: usa el umbral global | [G1-B-12](gate1-b/G1-B-12-concepto-sin-umbral.png) | Ok |
| 4 | HU-05 | Nombre de concepto repetido: rechazado (también con otras mayúsculas) | [G1-B-13](gate1-b/G1-B-13-concepto-repetido.png) <br> [G1-B-13b](gate1-b/G1-B-13b-concepto-repetido-minusculas.png) | Ok (ver observación 2) |
| 4 | HU-05 | Umbral 0 o negativo: rechazado | [G1-B-14](gate1-b/G1-B-14-umbral-0.png) | Ok |
| 4 | HU-06 | Plantilla de la propiedad con un concepto inactivo | [G1-B-15](gate1-b/G1-B-15-plantilla-seguro-inactivo.png) | Ok |
| 4 | HU-06 | Un concepto ya asociado no se puede asociar otra vez | [G1-B-15b](gate1-b/G1-B-15b-no-asocia-dos-veces.png) | Ok |
| 4 | HU-06 | Un concepto desactivado no aparece en el checklist que se abre después | [G1-B-15c](gate1-b/G1-B-15c-desactivado-no-aparece.png) | Ok |
| 14 | HU-02 | Alta de un usuario con rol operador | [G1-B-16](gate1-b/G1-B-16-alta-usuario.png) | Ok |
| 14 | HU-02 | Alta con un email existente: rechazada | [G1-B-17](gate1-b/G1-B-17-email-repetido.png) | Ok |
| 14 | HU-02 | Baja lógica: el usuario queda "De baja" y no se borra | [G1-B-18](gate1-b/G1-B-18-baja-usuario.png) | Ok |
| 14 | HU-02 | Un operador no puede gestionar usuarios | [G1-B-20](gate1-b/G1-B-20-operador-sin-permiso.png) | Ok |

### Observaciones

1. **Despliegue desactualizado.** Al empezar, el backend de Render seguía en el PR #12 porque no tenía activado el auto-deploy. Se redesplegó a mano con el último commit de `main` (`9924d90`). Conviene dejar activado el auto-deploy (Settings → Build & Deploy → Auto-Deploy: On Commit) para que cada merge se despliegue solo. El frontend de Vercel también tardó en actualizarse.
2. **Concepto repetido.** El primer intento mostró "No se pudo conectar con el servidor": Render todavía no tenía el PR #32 (nombre único sin distinguir mayúsculas, migración `001`), así que el backend respondía con un error interno. Después de redesplegar, el rechazo se muestra bien. Queda como mejora que un error interno (500) no se muestre como falta de conexión: hoy la respuesta 500 sale sin los encabezados CORS y el navegador la bloquea.
3. **Base reiniciada durante el Gate 1.** La base de Supabase se reinició con la semilla mientras se hacían las comprobaciones, por eso algunas capturas muestran datos distintos (por ejemplo, propiedades de prueba que después ya no están). La plantilla (HU-06) se probó con el concepto *Seguro* de la semilla.
4. **Datos de prueba.** El concepto "PRUEBA - Gate 1" y el usuario `prueba.gate1@tpfinalmail.com` (dado de baja) se crearon para estas comprobaciones.
