# Módulos funcionales — Sistema de asistencia para preliquidación de alquileres

Trabajo Final Integrador — modelo corregido (entrega final: 21 de noviembre)
Alumnos: Olima, Nicolás / Pannunzio, Nicolás

La aplicación asiste a la inmobiliaria en la carga y validación de conceptos variables y en el reparto entre propietarios. Produce una **preliquidación**: un resumen validado de conceptos variables con su reparto. La liquidación oficial sigue siendo la que genera Maru.

## Enumeración de módulos

| # | Módulo | Descripción | Prioridad |
|---|--------|-------------|-----------|
| 1 | **Autenticación de usuarios** | Login con Supabase Auth desde el frontend. El backend (FastAPI) valida el token en cada request y resuelve el usuario con `usuario.id`, que es el mismo UUID que `auth.users.id`. | Alta |
| 2 | **ABM de Propiedades y Propietarios** | Alta y edición de propiedades, propietarios y su relación de tenencia, con el % de reparto cuando hay varios propietarios sobre un mismo inmueble. Los porcentajes de una propiedad se reemplazan en una sola transacción y deben sumar 100 antes de confirmar. Es el dato maestro del que dependen los demás módulos. | Alta |
| 3 | **Gestión de conceptos variables (catálogo)** | ABM de los tipos de concepto (TGI, Aguas Santafesinas, API, Litoral Gas, EPE, expensas, seguros, etc.). Catálogo global, no por propiedad. Cada concepto puede definir un umbral propio de variación inusual. | Alta |
| 4 | **Plantilla de conceptos por propiedad** | Asocia a cada propiedad los conceptos que habitualmente le corresponden (activos o inactivos). Es la base desde la que se genera el checklist de cada período. | Alta |
| 5 | **Apertura de período y checklist mensual** | Al abrir un período para una propiedad se genera el checklist persistido: una fila por concepto activo, en estado `pendiente`. Cargar un importe lo pasa a `cargado`; el usuario puede marcar `no_corresponde` en cualquier momento, también sobre una fila ya `cargado`: en una transacción el backend borra el importe, guarda el valor anterior en `auditoria` y cambia el estado, sin alterar las preliquidaciones ya generadas. Distingue un importe de $0 (valor cargado) de un concepto pendiente o que no corresponde. | Alta |
| 6 | **Carga y validación de importes mensuales** | Alta de importes por concepto y período, con validación anti-duplicado y de inconsistencias. Admite importes negativos (notas de crédito) y $0. | Alta |
| 7 | **Cálculo de reparto entre propietarios** | Aplica el % vigente de la propiedad sobre el total y calcula el importe de cada propietario, redondeado a 2 decimales. El último propietario (por orden de id) absorbe el resto de centavos para que el reparto sume el total. | Alta |
| 8 | **Preliquidación mensual (snapshot versionado y consulta)** | Genera la preliquidación de una propiedad y un período: cabecera, detalle por concepto, reparto y advertencias, todo como snapshot inmutable. Bloquea la generación mientras haya conceptos pendientes, salvo confirmación explícita del usuario. Una corrección crea una versión nueva y conserva la anterior intacta; la vigente es la de mayor versión. Permite consultar el detalle y el reparto histórico por versión. | Alta |
| 9 | **Registro de auditoría** | Quién cargó o modificó qué, cuándo y sobre qué entidad. | Alta |
| 10 | **Gestión de usuarios y roles (UI propia)** | ABM de usuarios internos (alta, edición, baja lógica) y asignación de rol (admin/operador). El backend crea el usuario en Supabase Auth con la Admin API y luego inserta la fila en `usuario` con el mismo id. No se delega en el dashboard de Supabase. | Alta |
| 11 | **Advertencias de variación inusual y de datos faltantes** | Compara el importe cargado con el del período inmediato anterior para el mismo concepto y propiedad. Si la variación supera el umbral (el del concepto o, si no tiene, el global de 30 %), registra una advertencia no bloqueante. Sin período anterior, concepto nuevo o valor anterior 0, no advierte: deja solo una nota informativa "sin referencia". También advierte cuando el total de la preliquidación es negativo. | Media |

## Fuera de alcance

Los dos módulos adicionales de la entrega anterior (numerados 11 y 12) se excluyeron del alcance y la numeración se reordenó. El detalle está en la sección "Fuera de alcance / trabajo futuro" de [`arquitectura.md`](arquitectura.md).
