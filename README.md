# Sistema de Asistencia para Preliquidación de Alquileres

*Trabajo Final Integrador* — Tecnicatura Universitaria en Programación a Distancia (TUPAD)
Universidad Tecnológica Nacional · 2026

---

## Integrantes

| Rol | Nombre |
|---|---|
| Alumno | Olima, Nicolás |
| Alumno | Pannunzio, Nicolás |
| Tutor | Londero, Oscar |

---

## Sobre el proyecto

Herramienta web complementaria a Maru, el sistema de gestión de una *inmobiliaria real*. Asiste al personal administrativo en la carga y validación de los conceptos variables mensuales de cada propiedad (servicios, impuestos, expensas, seguros) y en su reparto entre propietarios.

El resultado es una **preliquidación**: un resumen validado de conceptos variables con su reparto. **No es la liquidación oficial**, que sigue generándose en Maru.

El sistema permite:
- Iniciar sesión con usuarios internos y roles (`admin` / `operador`)
- Gestionar propiedades, propietarios y el porcentaje de reparto de cada propiedad
- Definir el catálogo de conceptos y la plantilla de conceptos de cada propiedad
- Abrir un período y generar su checklist, para distinguir un concepto pendiente de un importe de $0 o de un concepto que no corresponde
- Cargar los importes del período, con rechazo de duplicados
- Recibir advertencias no bloqueantes por variación inusual, falta de referencia o total negativo
- Calcular el reparto entre propietarios
- Generar la preliquidación como snapshot inmutable y versionado: una corrección crea una versión nueva y conserva la anterior
- Consultar el detalle, las advertencias y el reparto de cada versión
- Registrar quién hizo cada operación y cuándo

> No reemplaza a Maru: lo complementa en la carga y validación de los conceptos variables mensuales.

**Fuera de alcance (trabajo futuro):** gestión de contratos e inquilinos, alertas de vencimiento y envío de emails.

---

## Tecnologías

| Componente | Stack |
|---|---|
| Frontend | TypeScript + React |
| Backend | Python + FastAPI |
| Base de datos | PostgreSQL (Supabase) |
| Autenticación | Supabase Auth |
| Comunicación | API REST (JSON) |
| Despliegue | Vercel (frontend) · Render (backend) · Supabase (base de datos y Auth) |
| Control de versiones | Git + GitHub |

---

## Estructura del repositorio

```
/backend     → API en FastAPI (app/core, app/audit, app/modules/<módulo>, tests)
/frontend    → Aplicación React (src/features/<módulo>, components, services, context, types)
/database    → Esquema de base de datos (esquema_completo.sql), seed y migraciones
/docs        → Documentación del proyecto
```

La documentación del modelo está en [`/docs`](docs):

- [`arquitectura.md`](docs/arquitectura.md)
- [`diagrama_ER.md`](docs/diagrama_ER.md)
- [`listado_modulos.md`](docs/listado_modulos.md)
- [`requerimientos.md`](docs/requerimientos.md)
- [`plan_implementacion.md`](docs/plan_implementacion.md)

---

## Variables de entorno

Cada componente tiene su propio `.env.example`, con los nombres de las variables y sin valores. Los archivos `.env` no se versionan.

---

## Estado

El proyecto está en la **Fase 0 (fundación)**: esqueleto del repositorio y documentación del modelo. Todavía no hay sistema desplegado.

Este README se completa en la fase final con:

- los enlaces al sistema desplegado, al Informe Final y al video;
- las instrucciones para ejecutar el sistema en local y correr las pruebas;
- la versión entregada (tag) y el detalle de lo implementado y lo proyectado.
