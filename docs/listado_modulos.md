# Módulos funcionales — Sistema de asistencia para liquidación de alquileres

Segunda entrega — Trabajo Final Integrador
Alumnos: Olima, Nicolás / Pannunzio, Nicolás

## Enumeración de módulos

| # | Módulo | Descripción | Prioridad |
|---|--------|-------------|-----------|
| 1 | **Autenticación de usuarios** | Login vía Supabase Auth; el backend (FastAPI) valida el token y resuelve el usuario autenticado en cada request. | Alta |
| 2 | **ABM de Propiedades y Propietarios** | Alta/edición de propiedades, propietarios y su relación de tenencia (incluyendo el % de reparto cuando hay grupos de propietarios sobre un mismo inmueble). Es el dato maestro del que dependen los demás módulos. | Alta |
| 3 | **Gestión de conceptos variables (catálogo)** | ABM de los tipos de concepto posibles (TGI, Aguas Santafesinas, API, Litoral Gas, EPE, expensas, seguros, etc.). Catálogo global, no por propiedad. | Alta |
| 4 | **Plantilla de conceptos por propiedad** | Asocia a cada propiedad los conceptos que habitualmente le corresponden. Es la base del checklist visual (cargado / pendiente) del período. | Alta |
| 5 | **Carga y validación de importes mensuales** | Alta de importes por concepto y período, con validaciones anti-duplicado e inconsistencias. | Alta |
| 6 | **Cálculo de reparto entre propietarios** | Aplica el % fijo de reparto (definido por propiedad) sobre los importes cargados y calcula lo que corresponde a cada propietario. | Alta |
| 7 | **Resumen / reporte mensual de liquidación** | Listado de liquidaciones del período con estado (cargada / con advertencia) e importe final por propiedad, para consulta y comunicación al inquilino. | Alta |
| 8 | **Registro de auditoría** | Quién cargó o modificó qué, cuándo, sobre qué entidad. | Alta |
| 9 | **Gestión de usuarios/roles (UI propia)** | ABM de usuarios internos (alta, edición, baja lógica) y asignación de rol (admin/operador), integrado con Supabase Auth. No se delega en el dashboard de Supabase. | Alta |
| 10 | **Alertas de variación inusual** | Compara el importe cargado contra el mes anterior y marca advertencia no bloqueante si la variación supera un umbral. También dispara advertencia cuando falta cargar un concepto marcado como activo para esa propiedad. | Media |
| 11 | **Gestión de contratos e inquilinos** | ABM de inquilinos (identificados de forma única por DNI) y de contratos por propiedad, con uno o más inquilinos por contrato. Los contratos se conservan como historial: al renovar se crea un contrato nuevo vinculado al anterior, que pasa a estado "renovado". Solo puede haber un contrato vigente por propiedad. Es el dato del que depende el módulo 12. | Media |
| 12 | **Alertas de vencimiento de contratos** | Evalúa diariamente los contratos vigentes y genera una alerta cuando faltan 20 días y otra cuando faltan 7 días para su vencimiento. Cada alerta se envía por email a los usuarios activos del sistema (registrando el envío para no repetirlo) y queda visible en el sistema con un estado (pendiente / en gestión / resuelta) para el seguimiento. El sistema solo avisa: el contacto con inquilinos y propietarios y la decisión de renovar quedan a cargo del personal administrativo. | Alta |