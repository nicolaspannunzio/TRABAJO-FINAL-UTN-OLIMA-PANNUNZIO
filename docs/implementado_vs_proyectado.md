# Implementado vs proyectado
 
Este documento es la fuente única de lo que está implementado y de lo que queda como proyectado. El informe final (sección 8, resultados y conclusiones) y el README se contrastan con esta tabla: lo que no figura acá como implementado no se declara como implementado.
 
Base: rama `main` al 20/11/2026. La versión entregada es la del tag de versión (Z8).
 
## Cómo leerlo
 
- **Implementado**: está en el código de `main`, corre en el sistema desplegado (Vercel + Render + Supabase) y tiene al menos una prueba automática o un paso del guion con evidencia.
- **Proyectado**: no se construyó. Coincide con la sección 10 de [`arquitectura.md`](arquitectura.md) y con el fuera de alcance de [`requerimientos.md`](requerimientos.md) (sección 2).
- **Pruebas automáticas**: rutas relativas a `backend/tests/`. El frontend no tiene pruebas automáticas; lo que se ve en pantalla se verifica con el guion.
- **Guion y evidencia**: pasos 1 a 14 del guion de [`plan_implementacion.md`](plan_implementacion.md) (sección 6). Las capturas de los pasos 5 a 14 y las del integrante B (pasos 1 a 4 y usuarios) están en [`evidencia/README.md`](evidencia/README.md).
## 1. Implementado por historia de usuario
 
| HU | Qué hace | Rutas | Pruebas automáticas | Guion y evidencia |
|---|---|---|---|---|
| HU-01 Iniciar sesión | Login con Supabase Auth; el backend valida el token en cada request, rechaza sin token (401) y al usuario inactivo (403 `usuario_inactivo`). El frontend guarda las rutas, redirige al login ante 401 y permite cerrar sesión. | `GET /me` y todas las rutas de datos | `test_auth.py`, `test_rutas_protegidas.py` (recorre `openapi.json`), `test_rls_anon.py` | Paso 1. Capturas G1-B-01, G1-B-02, G1-B-03 y G1-B-19. |
| HU-02 Gestionar usuarios | Alta (cuenta en Supabase Auth y fila en `usuario` con el mismo id, con compensación si falla), edición, baja lógica, auditoría, solo `admin`. | `GET/POST /usuarios`, `PATCH /usuarios/{id}`, `POST /usuarios/{id}/baja` | `usuarios/test_usuarios.py` | Paso 14 (alta o baja). Capturas G1-B-16 a G1-B-20. |
| HU-03 Propiedades y propietarios | Alta y edición de propiedades y propietarios; la propiedad nueva queda `activa`; un propietario no se repite en la misma propiedad. | `GET/POST /propiedades`, `GET/PATCH /propiedades/{id}`, `GET/POST /propietarios`, `GET/PATCH /propietarios/{id}` | `propiedades/test_propiedades_propietarios.py`, `propiedades/test_reparto.py` | Paso 2. Capturas G1-B-04 a G1-B-06. |
| HU-04 Porcentajes de reparto | Reemplazo transaccional de los porcentajes con validación de suma 100 antes del `COMMIT`; editor con la suma visible. Cambiar porcentajes no altera preliquidaciones ya generadas. | `GET/PUT /propiedades/{id}/propietarios` | `propiedades/test_reparto.py`, `propiedades/test_reparto_validacion.py`, `cross/test_gate1.py` | Paso 3. Capturas G1-B-07 a G1-B-10. |
| HU-05 Catálogo de conceptos | ABM con umbral opcional; nombre único sin distinguir mayúsculas; umbral mayor que 0. | `GET/POST /conceptos`, `PATCH /conceptos/{id}` | `conceptos/test_conceptos.py` | Paso 4. Capturas G1-B-11 a G1-B-14. |
| HU-06 Plantilla por propiedad | Asociar un concepto una sola vez por propiedad, activarlo o desactivarlo; el desactivado no entra en los checklists que se abren después. | `GET/POST /propiedades/{id}/conceptos`, `PATCH /propiedades/{id}/conceptos/{id}` | `plantilla/test_plantilla.py`, `cross/test_gate1.py` | Paso 4. Capturas G1-B-15, G1-B-15b y G1-B-15c. |
| HU-07 Abrir período | Una fila `pendiente` por concepto activo; período solo `AAAA-MM-01` (422 si no); abrir dos veces no duplica. | `POST/GET /checklist` | `checklist/test_abrir_periodo.py` | Paso 5. Captura paso-05. |
| HU-08 Cargar importes | Carga por fila, pasa a `cargado`, audita; admite negativos y $0; rechaza el duplicado (409) y el concepto sin fila en el checklist. | `POST /importes` | `importes/test_cargar_importe.py` | Pasos 6 y 7. Capturas paso-06, paso-07. |
| HU-09 No corresponde | Marca `no_corresponde` sin importe; si estaba `cargado`, borra el importe y audita el valor anterior; idempotente; las versiones ya generadas no cambian. | `POST /checklist/{fila_id}/no-corresponde` | `checklist/test_no_corresponde.py`, `preliquidaciones/test_generar.py` | Paso 8. Captura paso-08. |
| HU-10 Advertencias | Vista previa de `variacion_inusual` y `sin_referencia` contra el período anterior, con umbral propio o global; no persiste y nunca bloquea. | `GET /advertencias` | `advertencias/test_vista_previa.py`, `advertencias/test_calculo.py`, `preliquidaciones/test_generar.py` | Paso 9. Captura paso-09. |
| HU-11 Generar preliquidación | Bloquea con pendientes salvo confirmación (`pendiente_confirmado`); detalle solo con `cargado`; reparto con centavos al último por id; `total_negativo`; auditoría. | `POST /preliquidaciones` | `preliquidaciones/test_generar.py`, `reparto/test_repartir.py` | Pasos 10 y 11. Capturas paso-10, paso-11. |
| HU-12 Consultar preliquidaciones | Versiones, vigente (la de mayor versión) y detalle completo de una versión, sin depender de `auditoria`. | `GET /preliquidaciones`, `GET /preliquidaciones/vigente`, `GET /preliquidaciones/{id}` | `preliquidaciones/test_consultar.py` | Pasos 12 y 14. Capturas paso-12, paso-14. |
| HU-13 Corregir un importe | Modifica `importe_mensual` y guarda el valor anterior en `auditoria`; la versión ya generada no cambia. | `PATCH /importes/{id}` | `importes/test_corregir_importe.py` | Paso 13. Capturas paso-13. |
| HU-14 Nueva versión | Cada generación crea la versión siguiente y la anterior queda idéntica; la base rechaza `UPDATE`, `DELETE` y `TRUNCATE` sobre el snapshot. | `POST /preliquidaciones` | `preliquidaciones/test_nueva_version.py`, `preliquidaciones/test_generar.py`, `test_esquema.py` | Pasos 13 y 14. Capturas paso-13, paso-14. |
 
## 2. Implementado fuera de las HU
 
| Capacidad | Pruebas automáticas | Evidencia |
|---|---|---|
| Acceso solo por el backend con RLS activado y sin policies; la Data API con clave `anon` no devuelve filas (RN-04) | `test_rls_anon.py` | — |
| Auditoría de escrituras relevantes (RN-24) | `test_audit.py` y una prueba de auditoría en cada módulo que escribe | — |
| Snapshot inmutable por triggers (RN-23) | `test_esquema.py`, `preliquidaciones/test_nueva_version.py` | Paso 14 |
| Contrato: `docs/openapi.json` coincide con la aplicación y el formato de error es `{"codigo","mensaje","detalle"}` | `test_contrato.py`, `test_health.py` | CI en cada PR |
| Cálculo con `Decimal`, sin `float` (importes, reparto, variación) | `reparto/test_repartir.py`, `advertencias/test_calculo.py` | — |
| Integración continua: pytest, contrato, archivos generados, tipos, build y lint | `.github/workflows/ci.yml` | Checks de cada PR |
| Despliegue de los tres componentes (Supabase, Render, Vercel) | — | Paso 1; captura G1-B-00a (despliegue en Render) |
 
## 3. Reglas de negocio y su prueba
 
| RN | Prueba automática |
|---|---|
| RN-01 | `checklist/test_abrir_periodo.py::test_periodo_que_no_es_primer_dia_se_rechaza_con_422_sin_crear_filas` |
| RN-02 | `usuarios/test_usuarios.py::test_alta_crea_cuenta_y_fila_con_el_mismo_id`, `usuarios/test_usuarios.py::test_email_repetido_en_la_base_compensa_y_devuelve_409` |
| RN-03 | `usuarios/test_usuarios.py::test_baja_deja_activo_false_sin_borrar_la_fila_y_audita`, `usuarios/test_usuarios.py::test_usuario_dado_de_baja_recibe_403_usuario_inactivo` |
| RN-04 | `test_rls_anon.py::test_data_api_no_devuelve_filas`, `test_rls_anon.py::test_no_hay_policies`, `test_auth.py::test_sin_token_401`, `test_auth.py::test_token_invalido_401` |
| RN-05 | `propiedades/test_reparto.py::test_propietario_repetido_se_rechaza`, `propiedades/test_reparto.py::test_porcentaje_fuera_de_rango_se_rechaza` |
| RN-06 | `propiedades/test_reparto.py::test_cambiar_de_50_50_a_60_40`, `propiedades/test_reparto.py::test_suma_90_o_110_se_rechaza_y_conserva_lo_anterior`, `propiedades/test_reparto.py::test_un_fallo_a_mitad_conserva_los_porcentajes_anteriores`, `propiedades/test_reparto.py::test_nunca_se_lee_un_estado_intermedio`, `cross/test_gate1.py::test_cambiar_porcentajes_no_altera_una_preliquidacion_generada` |
| RN-07 | `conceptos/test_conceptos.py::test_nombre_repetido_con_otras_mayusculas_se_rechaza_409`, `conceptos/test_conceptos.py::test_umbral_invalido_se_rechaza_422` |
| RN-08 | `plantilla/test_plantilla.py::test_asociar_dos_veces_se_rechaza_409_y_queda_una_sola_fila` |
| RN-09 | `checklist/test_abrir_periodo.py::test_abrir_crea_una_fila_pendiente_por_concepto_activo`, `checklist/test_abrir_periodo.py::test_abrir_dos_veces_no_duplica_filas` |
| RN-10 | `importes/test_cargar_importe.py::test_cargar_importe_pasa_la_fila_a_cargado_y_audita`, `checklist/test_no_corresponde.py::test_cero_y_no_corresponde_se_muestran_distintos` |
| RN-11 | `importes/test_cargar_importe.py::test_concepto_inactivo_sin_fila_se_rechaza`, `importes/test_cargar_importe.py::test_periodo_sin_abrir_se_rechaza` |
| RN-12 | `importes/test_cargar_importe.py::test_importe_duplicado_se_rechaza_con_409_y_conserva_el_primero` |
| RN-13 | `importes/test_cargar_importe.py::test_importe_negativo_o_cero_se_acepta`, `preliquidaciones/test_generar.py::test_total_negativo_advierte_y_reparte_negativo` |
| RN-14 | `importes/test_corregir_importe.py::test_corregir_actualiza_el_importe_y_audita_el_valor_anterior`, `importes/test_corregir_importe.py::test_la_version_1_sigue_mostrando_el_importe_original` |
| RN-15 | `advertencias/test_vista_previa.py::test_vista_previa_aplica_los_criterios_de_hu10`, `advertencias/test_calculo.py::test_umbral_efectivo_usa_el_propio_si_existe_y_si_no_el_global` |
| RN-16 | `advertencias/test_vista_previa.py::test_vista_previa_aplica_los_criterios_de_hu10`, `advertencias/test_calculo.py::test_evaluar` |
| RN-17 | `preliquidaciones/test_generar.py::test_las_advertencias_de_variacion_no_impiden_generar_y_quedan_guardadas` |
| RN-18 | `preliquidaciones/test_generar.py::test_con_pendiente_sin_confirmar_no_genera_e_informa_el_pendiente`, `preliquidaciones/test_generar.py::test_confirmando_genera_la_version_1_con_un_pendiente_confirmado_por_pendiente` |
| RN-19 | `preliquidaciones/test_generar.py::test_detalle_solo_con_cargados_y_total_es_la_suma` |
| RN-20 | `preliquidaciones/test_generar.py::test_total_negativo_advierte_y_reparte_negativo` |
| RN-21 | `preliquidaciones/test_generar.py::test_reparto_de_10_pesos_en_tercios`, `reparto/test_repartir.py::test_el_ultimo_por_id_absorbe_la_diferencia`, `reparto/test_repartir.py::test_la_suma_siempre_es_el_total` |
| RN-22 | `preliquidaciones/test_consultar.py::test_con_versiones_1_y_2_la_vigente_es_la_2`, `preliquidaciones/test_generar.py::test_generar_otra_vez_crea_la_version_2`, `preliquidaciones/test_generar.py::test_choque_de_version_responde_409_sin_dejar_nada_a_medias` |
| RN-23 | `preliquidaciones/test_nueva_version.py::test_la_base_rechaza_modificar_el_snapshot`, `test_esquema.py::test_trigger_rechaza_modificar_preliquidacion`, `preliquidaciones/test_nueva_version.py::test_la_version_1_queda_identica_despues_de_generar_la_2` |
| RN-24 | `usuarios/test_usuarios.py::test_alta_audita_con_el_admin_y_sin_la_contrasena`, `preliquidaciones/test_generar.py::test_la_generacion_queda_auditada`, `usuarios/test_usuarios.py::test_editar_nombre_y_rol_audita_antes_y_despues` |
| RN-25 | `checklist/test_no_corresponde.py::test_marcar_cargado_borra_el_importe_y_audita_el_valor_anterior`, `preliquidaciones/test_generar.py::test_no_corresponde_despues_de_v1_no_cambia_v1_y_v2_no_lo_incluye` |
 
## 4. Proyectado (no implementado)
 
| Elemento | Estado | Dónde está documentado |
|---|---|---|
| Gestión de contratos e inquilinos (tablas `inquilino`, `contrato`, `contrato_inquilino`) | Proyectado | `arquitectura.md` sección 10 |
| Alertas de vencimiento de contratos (tabla `alerta_vencimiento`) | Proyectado | `arquitectura.md` sección 10 |
| Envío de emails y elección de un proveedor de email | Proyectado | `arquitectura.md` sección 10 |
| Integración con WhatsApp (generar el texto y abrir el chat, con confirmación humana) | Proyectado | `arquitectura.md` sección 10 |
| Vigencia temporal de los porcentajes de reparto (hoy hay un solo porcentaje vigente por propietario y propiedad; la preliquidación guarda el `porcentaje_aplicado`) | Proyectado | `arquitectura.md` sección 10 |
| Integración técnica con Maru | Proyectado | `requerimientos.md` sección 2 |
| Carga del alquiler base y reconstrucción de la liquidación que ya calcula Maru | Proyectado | `requerimientos.md` sección 2 |
 
Comprobación hecha sobre `main`: el esquema tiene 14 tablas, ninguna de contratos, inquilinos ni alertas, y `docs/openapi.json` no publica rutas de esos temas, de emails ni de WhatsApp.
 
## 5. Implementado, con límites o a confirmar
 
Estos puntos se declaran en el informe como limitaciones conocidas.
 
- **Umbral global de 30 % (RN-15)**: valor inicial, configurable con `UMBRAL_VARIACION_DEFAULT_PCT`. A confirmar con la inmobiliaria.
- **Bloqueo de la generación con pendientes y su confirmación (RN-18)**: a confirmar con la inmobiliaria.
- **Contraseña inicial**: no hay cambio forzado en el primer ingreso.
- **Dos administradores que se dan de baja entre sí al mismo tiempo**: podrían quedar sin ningún admin activo; se recupera a mano desde Supabase.
- **Compensación fallida del alta**: si falla el borrado de la cuenta de Auth, queda una cuenta huérfana; se loguea su id.
- **Error interno (500) en el frontend**: se muestra como "No se pudo conectar con el servidor", porque esa respuesta sale sin encabezados CORS.
- **Arranque en frío de Render**: la primera request puede tardar; hay que calentar el backend antes de la demo.
 