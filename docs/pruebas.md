# Matriz de pruebas

Unidad Z3 del [plan de implementación](plan_implementacion.md). Para cada criterio de aceptación de las 14 historias de usuario de [`requerimientos.md`](requerimientos.md) (sección 7), esta matriz indica qué prueba lo verifica y con qué resultado.

## Cómo leer la matriz

- **Prueba automática:** test de `pytest` en `backend/tests/`, con el formato `archivo::nombre_del_test`. Corren contra un PostgreSQL local descartable al que se le carga [`database/esquema_completo.sql`](../database/esquema_completo.sql), con los mismos triggers y restricciones que Supabase. La CI ([`.github/workflows/ci.yml`](../.github/workflows/ci.yml)) los corre en cada PR contra PostgreSQL 17.
- **Verificación manual:** comprobación sobre el sistema desplegado (Vercel + Render + Supabase), con su captura en [`evidencia/`](evidencia/README.md). Los pasos son los del guion del recorrido del tutor (plan, sección 6).
- **Resultado:** ✅ pasa · ❌ falla · ⚠️ sin cubrir.

## 1. Resumen

| | Cantidad |
|---|---|
| Criterios de aceptación (14 HU) | 48 |
| Con prueba automática | 47 |
| Solo con verificación manual | 1 (HU-09, criterio 5: confirmación en pantalla) |
| Sin cubrir | 0 |
| Tests automáticos del backend | 338, en 24 archivos |
| Resultado | **338 passed, 0 failed** (sección 5) |

Además de la prueba automática, 36 de los 48 criterios tienen una verificación manual sobre el sistema desplegado.

## 2. Matriz por historia de usuario

Rutas abreviadas: los tests están en `backend/tests/` y las capturas en `docs/evidencia/`.

### HU-01. Iniciar sesión

| # | Criterio | Prueba automática | Verificación manual | Resultado |
|---|---|---|---|---|
| 1 | Con credenciales válidas accede y cada request lleva su token | `test_auth.py::test_propiedades_requiere_token_y_lista`, `test_auth.py::test_me_devuelve_usuario_y_rol` | Paso 1 · [G1-B-01](evidencia/gate1-b/G1-B-01-login-ok-01.png) | ✅ |
| 2 | Sin token o con token inválido: 401 y sin datos | `test_auth.py`: `test_sin_token_401`, `test_token_invalido_401`, `test_token_expirado_401`, `test_token_firmado_con_otro_secreto_401` y otros 6 casos; `test_rutas_protegidas.py` recorre todas las rutas de `openapi.json` | Paso 1 · [G1-B-02](evidencia/gate1-b/G1-B-02-sin-token-401.png) | ✅ |
| 3 | Usuario con `activo = false`: 403 `usuario_inactivo` | `test_auth.py::test_usuario_inactivo_403`, `usuarios/test_usuarios.py::test_usuario_dado_de_baja_recibe_403_usuario_inactivo`, `test_rutas_protegidas.py` | Paso 14 · [G1-B-19](evidencia/gate1-b/G1-B-19-inactivo-rechazado.png) | ✅ |
| 4 | Data API con la clave `anon`: ninguna fila | `test_rls_anon.py::test_data_api_no_devuelve_filas` (roles `anon` y `authenticated`), `test_rls_anon.py::test_no_hay_policies` | — | ✅ |

### HU-02. Gestionar usuarios

| # | Criterio | Prueba automática | Verificación manual | Resultado |
|---|---|---|---|---|
| 1 | El alta crea la cuenta en Auth y la fila en `usuario` con el mismo id y rol | `usuarios/test_usuarios.py::test_alta_crea_cuenta_y_fila_con_el_mismo_id`, `::test_alta_audita_con_el_admin_y_sin_la_contrasena` | Paso 14 · [G1-B-16](evidencia/gate1-b/G1-B-16-alta-usuario.png) | ✅ |
| 2 | Si falla el insert en `usuario`, no queda la cuenta en Auth | `usuarios/test_usuarios.py::test_email_repetido_en_la_base_compensa_y_devuelve_409`, `::test_fallo_inesperado_del_insert_compensa_y_devuelve_500`, `::test_si_falla_la_compensacion_igual_responde_500` | Paso 14 · [G1-B-17](evidencia/gate1-b/G1-B-17-email-repetido.png) | ✅ |
| 3 | La baja deja `activo = false`, no borra la fila y se audita | `usuarios/test_usuarios.py::test_baja_deja_activo_false_sin_borrar_la_fila_y_audita`, `::test_baja_es_idempotente_y_no_audita_dos_veces` | Paso 14 · [G1-B-18](evidencia/gate1-b/G1-B-18-baja-usuario.png) | ✅ |
| 4 | Un admin no puede darse de baja ni cambiarse el rol (409 `autoedicion_no_permitida`); sí su nombre, y sí a otro admin | `usuarios/test_usuarios.py::test_admin_no_puede_darse_de_baja_a_si_mismo`, `::test_admin_no_puede_cambiarse_el_propio_rol`, `::test_admin_si_puede_editar_su_propio_nombre`, `::test_admin_si_puede_dar_de_baja_a_otro_admin` | — | ✅ |

### HU-03. Registrar propiedades y propietarios

| # | Criterio | Prueba automática | Verificación manual | Resultado |
|---|---|---|---|---|
| 1 | Una propiedad nueva queda `activa` | `propiedades/test_propiedades_propietarios.py::test_propiedad_nueva_queda_activa` | Paso 2 · [G1-B-05](evidencia/gate1-b/G1-B-05-propiedad-nueva-activa.png) | ✅ |
| 2 | Un propietario no se asocia dos veces a la misma propiedad | `propiedades/test_reparto.py::test_propietario_repetido_se_rechaza`, `propiedades/test_reparto_validacion.py::test_propietario_repetido_se_rechaza` | Paso 2 · [G1-B-06](evidencia/gate1-b/G1-B-06-no-repite-propietario.png) | ✅ |

### HU-04. Definir porcentajes de reparto

| # | Criterio | Prueba automática | Verificación manual | Resultado |
|---|---|---|---|---|
| 1 | De 50/50 a 60/40 sin estados intermedios | `propiedades/test_reparto.py::test_cambiar_de_50_50_a_60_40`, `::test_nunca_se_lee_un_estado_intermedio`, `::test_un_fallo_a_mitad_conserva_los_porcentajes_anteriores` | Paso 3 · [G1-B-09](evidencia/gate1-b/G1-B-09-reparto-60-40.png) | ✅ |
| 2 | Suma 90 o 110: se rechaza y se conservan los anteriores | `propiedades/test_reparto.py::test_suma_90_o_110_se_rechaza_y_conserva_lo_anterior` (2 casos), `propiedades/test_reparto_validacion.py::test_suma_distinta_de_100_se_rechaza` (4 casos) | Paso 3 · [G1-B-07](evidencia/gate1-b/G1-B-07-suma-90-rechazada.png) | ✅ |
| 3 | Porcentaje 0 o mayor que 100: se rechaza | `propiedades/test_reparto.py::test_porcentaje_fuera_de_rango_se_rechaza` (5 casos) | Paso 3 · [G1-B-08](evidencia/gate1-b/G1-B-08-porcentaje-0.png) | ✅ |
| 4 | Cambiar a 60/40 no altera una preliquidación ya generada con 50/50 | `cross/test_gate1.py::test_cambiar_porcentajes_no_altera_una_preliquidacion_generada` | — | ✅ |

### HU-05. Mantener el catálogo de conceptos

| # | Criterio | Prueba automática | Verificación manual | Resultado |
|---|---|---|---|---|
| 1 | Nombre existente: se rechaza (también con otras mayúsculas, RN-07) | `conceptos/test_conceptos.py::test_nombre_repetido_se_rechaza_409`, `::test_nombre_repetido_con_otras_mayusculas_se_rechaza_409`, `::test_editar_con_nombre_de_otro_concepto_409` | Paso 4 · [G1-B-13](evidencia/gate1-b/G1-B-13-concepto-repetido.png), [G1-B-13b](evidencia/gate1-b/G1-B-13b-concepto-repetido-minusculas.png) | ✅ |
| 2 | Sin umbral: queda `NULL` y usa el global | `conceptos/test_conceptos.py::test_concepto_sin_umbral_queda_null`, `::test_editar_umbral_null_vuelve_al_global` | Paso 4 · [G1-B-12](evidencia/gate1-b/G1-B-12-concepto-sin-umbral.png) | ✅ |
| 3 | Umbral 0 o negativo: se rechaza | `conceptos/test_conceptos.py::test_umbral_invalido_se_rechaza_422` (7 casos) | Paso 4 · [G1-B-14](evidencia/gate1-b/G1-B-14-umbral-0.png) | ✅ |

### HU-06. Asociar conceptos a una propiedad

| # | Criterio | Prueba automática | Verificación manual | Resultado |
|---|---|---|---|---|
| 1 | Un concepto ya asociado no se asocia otra vez | `plantilla/test_plantilla.py::test_asociar_dos_veces_se_rechaza_409_y_queda_una_sola_fila`, `::test_asociar_un_concepto_desactivado_tambien_se_rechaza` | Paso 4 · [G1-B-15b](evidencia/gate1-b/G1-B-15b-no-asocia-dos-veces.png) | ✅ |
| 2 | Un concepto desactivado no aparece en los checklist que se abren después | `cross/test_gate1.py::test_concepto_desactivado_no_aparece_en_el_checklist_que_se_abre_despues` | Paso 4 · [G1-B-15c](evidencia/gate1-b/G1-B-15c-desactivado-no-aparece.png) | ✅ |

### HU-07. Abrir un período

| # | Criterio | Prueba automática | Verificación manual | Resultado |
|---|---|---|---|---|
| 1 | 4 activos y 1 inactivo: 4 filas `pendiente` con período `2026-09-01` | `checklist/test_abrir_periodo.py::test_abrir_crea_una_fila_pendiente_por_concepto_activo` | Paso 5 · [paso-05](evidencia/paso-05-abrir-periodo.png) | ✅ |
| 2 | Período que no es día 1: 422, sin filas y sin normalizar | `checklist/test_abrir_periodo.py::test_periodo_que_no_es_primer_dia_se_rechaza_con_422_sin_crear_filas` | — | ✅ |
| 3 | Abrir dos veces no duplica filas | `checklist/test_abrir_periodo.py::test_abrir_dos_veces_no_duplica_filas` | — | ✅ |

### HU-08. Cargar importes

| # | Criterio | Prueba automática | Verificación manual | Resultado |
|---|---|---|---|---|
| 1 | Cargar $15.000: la fila pasa a `cargado` y se audita con el usuario | `importes/test_cargar_importe.py::test_cargar_importe_pasa_la_fila_a_cargado_y_audita` | Paso 6 · [paso-06](evidencia/paso-06-carga-importes.png) | ✅ |
| 2 | Duplicado: se rechaza con mensaje y se conserva el primero | `importes/test_cargar_importe.py::test_importe_duplicado_se_rechaza_con_409_y_conserva_el_primero` | Paso 7 · [paso-07](evidencia/paso-07-importe-original.png), [paso-07.1](evidencia/paso-07-duplicado-409.png) (ver sección 6, nota 4) | ✅ |
| 3 | −$2.000 y $0 se aceptan | `importes/test_cargar_importe.py::test_importe_negativo_o_cero_se_acepta` (2 casos) | Paso 6 · [paso-06](evidencia/paso-06-carga-importes.png) | ✅ |
| 4 | Concepto sin fila en el checklist: se rechaza | `importes/test_cargar_importe.py::test_concepto_inactivo_sin_fila_se_rechaza`, `::test_periodo_sin_abrir_se_rechaza` | — | ✅ |

### HU-09. Marcar un concepto como no corresponde

| # | Criterio | Prueba automática | Verificación manual | Resultado |
|---|---|---|---|---|
| 1 | `pendiente` pasa a `no_corresponde` sin importe | `checklist/test_no_corresponde.py::test_marcar_pendiente_pasa_a_no_corresponde_sin_importe` | — | ✅ |
| 2 | $0 y `no_corresponde` se muestran como estados distintos | `checklist/test_no_corresponde.py::test_cero_y_no_corresponde_se_muestran_distintos` | Paso 8 · [paso-08](evidencia/paso-08-no-corresponde.png) | ✅ |
| 3 | `cargado` con importe X: se borra el importe y `auditoria` guarda X, usuario y fecha | `checklist/test_no_corresponde.py::test_marcar_cargado_borra_el_importe_y_audita_el_valor_anterior`, `::test_si_falla_la_auditoria_no_se_borra_el_importe` | — | ✅ |
| 4 | Con v1 generada, marcar y generar v2: v2 no lo tiene y v1 no cambia | `preliquidaciones/test_generar.py::test_no_corresponde_despues_de_v1_no_cambia_v1_y_v2_no_lo_incluye` | — | ✅ |
| 5 | La pantalla pide confirmación (avisa si se elimina el importe); al cancelar no cambia nada | — (el frontend no tiene tests automáticos) | Verificación manual registrada en el PR #18 (capturas de B3) | ✅ |

### HU-10. Revisar advertencias de variación

| # | Criterio | Prueba automática | Verificación manual | Resultado |
|---|---|---|---|---|
| 1 | $1.000 → $1.350 (35 %): `variacion_inusual`; → $1.200 (20 %): no | `advertencias/test_calculo.py::test_evaluar` (casos "35 % con umbral global" y "20 % con umbral global"), `advertencias/test_vista_previa.py::test_vista_previa_aplica_los_criterios_de_hu10` | Paso 9 · [paso-09](evidencia/paso-09-advertencias.png) | ✅ |
| 2 | Umbral propio 50 %: $1.350 no advierte | `advertencias/test_calculo.py::test_evaluar` (caso "35 % con umbral propio 50"), `test_vista_previa.py::test_vista_previa_aplica_los_criterios_de_hu10` | Paso 9 · [paso-09](evidencia/paso-09-advertencias.png) | ✅ |
| 3 | $1.000 → −$200 (120 %): `variacion_inusual` | `advertencias/test_calculo.py::test_evaluar` (caso "1000 a -200 (120 %)"), `test_vista_previa.py::test_vista_previa_aplica_los_criterios_de_hu10` | Paso 9 · [paso-09](evidencia/paso-09-advertencias.png) | ✅ |
| 4 | Sin importe anterior o anterior en $0: solo `sin_referencia` | `advertencias/test_calculo.py::test_evaluar` (casos "sin importe anterior" y "anterior en 0"), `test_vista_previa.py::test_vista_previa_aplica_los_criterios_de_hu10` | Paso 9 · [paso-09](evidencia/paso-09-advertencias.png) | ✅ |
| 5 | Ninguna advertencia impide generar | `preliquidaciones/test_generar.py::test_las_advertencias_de_variacion_no_impiden_generar_y_quedan_guardadas` | Paso 11 · [paso-11](evidencia/paso-11-version-2.png) | ✅ |

### HU-11. Generar la preliquidación

| # | Criterio | Prueba automática | Verificación manual | Resultado |
|---|---|---|---|---|
| 1 | Con un pendiente y sin confirmar: no genera e informa el pendiente | `preliquidaciones/test_generar.py::test_con_pendiente_sin_confirmar_no_genera_e_informa_el_pendiente` | Paso 10 · [paso-10](evidencia/paso-10-bloqueo-pendiente.png) | ✅ |
| 2 | Confirmando: versión 1 con una `pendiente_confirmado` por pendiente | `preliquidaciones/test_generar.py::test_confirmando_genera_la_version_1_con_un_pendiente_confirmado_por_pendiente` | Paso 10 · [paso-10.1](evidencia/paso-10-bloqueo-pendiente-preliquidacion-generada.png) | ✅ |
| 3 | $8.000, $0, $2.000 y uno `no_corresponde`: 3 filas y total $10.000 | `preliquidaciones/test_generar.py::test_detalle_solo_con_cargados_y_total_es_la_suma` | — | ✅ |
| 4 | $10,00 con 33,33 / 33,33 / 33,34: 3,33 / 3,33 / 3,34 por id, suma exacta | `preliquidaciones/test_generar.py::test_reparto_de_10_pesos_en_tercios`; `reparto/test_repartir.py` (18 casos, incluida una prueba de 2.000 repartos al azar) | Paso 11 · [paso-11](evidencia/paso-11-version-2.png) | ✅ |
| 5 | Total −$500: `total_negativo` y reparto negativo | `preliquidaciones/test_generar.py::test_total_negativo_advierte_y_reparte_negativo`, `reparto/test_repartir.py::test_repartir` (caso "total negativo 50/50") | — | ✅ |

### HU-12. Consultar preliquidaciones

| # | Criterio | Prueba automática | Verificación manual | Resultado |
|---|---|---|---|---|
| 1 | Con versiones 1 y 2, la vigente es la 2 | `preliquidaciones/test_consultar.py::test_con_versiones_1_y_2_la_vigente_es_la_2` | Paso 14 · [paso-14](evidencia/paso-14-vigente-y-anteriores.png) | ✅ |
| 2 | La versión 1 se ve tal como se generó, sin depender de `auditoria` | `preliquidaciones/test_consultar.py::test_la_version_1_se_ve_como_se_genero_sin_depender_de_auditoria` | Paso 12 · [paso-12](evidencia/paso-12-consulta-versiones-1.png), [paso-12.1](evidencia/paso-12-consulta-versiones-2.png) | ✅ |

### HU-13. Corregir un importe ya preliquidado

| # | Criterio | Prueba automática | Verificación manual | Resultado |
|---|---|---|---|---|
| 1 | $86.200 → $68.200: queda corregido y `auditoria` registra el anterior, usuario y fecha | `importes/test_corregir_importe.py::test_corregir_actualiza_el_importe_y_audita_el_valor_anterior`, `::test_si_falla_la_auditoria_el_importe_no_cambia` | Paso 13 · [paso-13](evidencia/paso-13-correccion-version-3.png) | ✅ |
| 2 | La versión 1 sigue mostrando $86.200 | `importes/test_corregir_importe.py::test_la_version_1_sigue_mostrando_el_importe_original` | Paso 14 · [paso-14](evidencia/paso-14-vigente-y-anteriores.png) | ✅ |

### HU-14. Generar una nueva versión

| # | Criterio | Prueba automática | Verificación manual | Resultado |
|---|---|---|---|---|
| 1 | Regenerar crea la versión 2 con el importe corregido y pasa a ser la vigente | `preliquidaciones/test_nueva_version.py::test_regenerar_crea_la_version_2_con_el_importe_corregido_y_es_la_vigente` | Paso 13 · [paso-13.1](evidencia/paso-13.1-correccion-version-3.png) | ✅ |
| 2 | La versión 1 queda idéntica después de generar la 2 | `preliquidaciones/test_nueva_version.py::test_la_version_1_queda_identica_despues_de_generar_la_2` (compara la API y cada fila de las 4 tablas) | Paso 14 · [paso-14](evidencia/paso-14-vigente-y-anteriores.png) | ✅ |
| 3 | La base rechaza `UPDATE`, `DELETE` y `TRUNCATE` sobre las 4 tablas del snapshot | `preliquidaciones/test_nueva_version.py::test_la_base_rechaza_modificar_el_snapshot` (12 casos: 4 tablas × 3 operaciones), `test_esquema.py::test_trigger_rechaza_modificar_preliquidacion` | — | ✅ |

## 3. Pruebas que no corresponden a un criterio puntual

Cubren reglas transversales del plan y de la arquitectura.

| Qué se prueba | Tests |
|---|---|
| Contrato: el 422 usa `{codigo, mensaje, detalle}` y `docs/openapi.json` coincide con la aplicación | `test_contrato.py` |
| Formato de error de una ruta sin implementar (501) | `test_health.py::test_stub_devuelve_formato_de_error` |
| `GET /health` con chequeo de base | `test_health.py::test_health_ok` |
| El esquema de los tests sale del SQL, sin `create_all()` | `test_esquema.py::test_esquema_cargado_desde_sql` |
| La auditoría se guarda o se descarta junto con la operación | `test_audit.py` |
| Atomicidad: si falla la auditoría, no queda nada a medias | `importes/test_cargar_importe.py::test_si_falla_la_auditoria_no_queda_nada` y los tests `..._si_falla_la_auditoria_...` de HU-09 y HU-13 |
| Dos generaciones simultáneas: una recibe 409 `version_en_conflicto` y no quedan filas sueltas | `preliquidaciones/test_generar.py::test_choque_de_version_responde_409_sin_dejar_nada_a_medias` |
| Importes como cadena decimal, nunca `float` | `importes/test_cargar_importe.py::test_importe_como_numero_se_rechaza_con_422`, `importes/test_corregir_importe.py::test_importe_como_numero_se_rechaza_con_422`, `advertencias/test_calculo.py::test_todo_en_decimal_sin_float`, `reparto/test_repartir.py::test_todo_en_decimal_con_dos_decimales` |
| El operador no gestiona usuarios (RN-02) | `test_auth.py::test_operador_rechazado_por_require_admin`, `usuarios/test_usuarios.py::test_operador_recibe_403_y_no_se_crea_nada` · manual [G1-B-20](evidencia/gate1-b/G1-B-20-operador-sin-permiso.png) |

## 4. Inventario de tests por archivo

Casos ejecutados por `pytest` (un test parametrizado cuenta una vez por caso).

| Archivo | Unidad | Casos |
|---|---|---|
| `test_auth.py`, `test_audit.py`, `test_contrato.py`, `test_esquema.py`, `test_health.py` | Fase 0 | 15 + 2 + 4 + 3 + 2 = 26 |
| `test_rls_anon.py`, `test_rutas_protegidas.py` | A1 | 3 + 94 = 97 |
| `usuarios/test_usuarios.py` | A2 | 27 |
| `propiedades/test_propiedades_propietarios.py` | A3 | 22 |
| `propiedades/test_reparto.py`, `propiedades/test_reparto_validacion.py` | A4 | 15 + 6 = 21 |
| `conceptos/test_conceptos.py` | A5 | 27 |
| `plantilla/test_plantilla.py` | A6 | 13 |
| `checklist/test_abrir_periodo.py` | B1 | 6 |
| `importes/test_cargar_importe.py` | B2 | 9 |
| `checklist/test_no_corresponde.py` | B3 | 6 |
| `advertencias/test_calculo.py`, `advertencias/test_vista_previa.py` | B4 | 14 + 5 = 19 |
| `reparto/test_repartir.py` | B5 | 18 |
| `preliquidaciones/test_generar.py` | B6 | 14 |
| `preliquidaciones/test_consultar.py` | B7 | 7 |
| `importes/test_corregir_importe.py` | B8 | 10 |
| `preliquidaciones/test_nueva_version.py` | B9 | 14 |
| `cross/test_gate1.py` | Gate 1 | 2 |
| **Total** | | **338** |

## 5. Comandos ejecutados y resultado

Ejecutados sobre `main` en el commit `eb2f593`.

Entorno: Windows con PowerShell, Python 3.13, PostgreSQL local descartable (base terminada en `_test`) y Node con las dependencias de `package-lock.json`.

### Backend

```text
> cd backend
> pytest
...
======================= 338 passed, 1 warning in 33.60s =======================
```

La única advertencia es de una librería (`starlette.testclient` recomienda instalar `httpx2`) y no afecta los resultados.

### Frontend

```text
> cd frontend
> npm run lint

> frontend@0.0.0 lint
> eslint .

> npx tsc -b
(sin salida: no hay errores de tipos)

> npx vite build
vite v8.3.8 building client environment for production...
✓ 288 modules transformed.
dist/index.html                  0.39 kB │ gzip:   0.27 kB
dist/assets/index-Dg3p8QD-.js  709.68 kB │ gzip: 197.86 kB

(!) Some chunks are larger than 500 kB after minification.
✓ built in 700ms
```

Lint y chequeo de tipos sin errores. El build termina bien; el aviso de tamaño se comenta en la sección 6.

### CI

Cada PR corre `pytest`, la regeneración y comparación de `docs/openapi.json`, `types/api.ts` y `routeTree.gen.ts`, el chequeo de tipos y el lint del frontend ([`ci.yml`](../.github/workflows/ci.yml)).

## 6. Limitaciones y notas

1. **El frontend no tiene tests automáticos.** El proyecto no incluye un runner de tests para React. Lo que depende solo de la pantalla (por ejemplo, la confirmación de HU-09 criterio 5 o el aviso de duplicado) se verificó a mano. El chequeo de tipos (`tsc`), el lint y el build sí corren en cada PR.
2. **Supabase Auth simulado en HU-02.** Los tests de usuarios reemplazan la Admin API de Supabase por un cliente simulado. El alta real contra Supabase se verificó a mano en el sistema desplegado ([G1-B-16](evidencia/gate1-b/G1-B-16-alta-usuario.png)).
3. **HU-01 criterio 4 en local.** El test reproduce los roles `anon` y `authenticated` de Supabase en el PostgreSQL de pruebas, con RLS activada y sin policies, igual que en Supabase. No hace una llamada real a la Data API.
4. **Aviso de duplicado (HU-08, criterio 2).** En el recorrido del Gate 1 el rechazo funcionaba, pero el aviso en pantalla desaparecía casi al instante (issue #36). Se corrigió en el PR #40: ahora el aviso queda visible hasta cerrarlo.
5. **Concurrencia simulada.** El choque de dos generaciones simultáneas se prueba forzando el mismo número de versión, en lugar de lanzar dos requests en paralelo: así el resultado es siempre el mismo.
6. **Limpieza del snapshot en los tests.** Las tablas de la preliquidación no se pueden modificar. Para limpiar después de cada test, los tests apagan los triggers solo en su conexión a la base de pruebas (`session_replication_role = replica`). Nunca se hace fuera de los tests.
7. **Tamaño del bundle del frontend.** El build avisa que el JavaScript de la aplicación pesa unos 710 kB (198 kB comprimido), por encima del umbral de 500 kB que sugiere Vite. No es un error: la aplicación se construye y funciona. Queda como mejora posible dividir el código por pantalla (*code splitting*) para que la primera carga sea más rápida.
