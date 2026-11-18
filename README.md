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
| Frontend | TypeScript + React 19, Vite, TanStack (Router, Query, Form, Table) |
| Backend | Python 3.13 + FastAPI |
| Base de datos | PostgreSQL (Supabase) |
| Autenticación | Supabase Auth |
| Comunicación | API REST (JSON), contrato en `docs/openapi.json` |
| Pruebas | pytest (backend) · chequeo de tipos y ESLint (frontend) |
| Integración continua | GitHub Actions |
| Despliegue | Vercel (frontend) · Render (backend) · Supabase (base de datos y Auth) |
| Control de versiones | Git + GitHub |
 
---
 
## Estructura del repositorio
 
```
/backend     → API en FastAPI (app/core, app/audit, app/modules/<módulo>, scripts, tests)
/frontend    → Aplicación React (src/features/<módulo>, components, services, context, types)
/database    → Esquema de base de datos (esquema_completo.sql) y seed
/docs        → Documentación del proyecto y contrato de la API (openapi.json)
/.github     → Workflow de CI
```
 
La documentación del modelo está en [`/docs`](docs):
 
- [`arquitectura.md`](docs/arquitectura.md)
- [`diagrama_ER.md`](docs/diagrama_ER.md)
- [`listado_modulos.md`](docs/listado_modulos.md)
- [`requerimientos.md`](docs/requerimientos.md)
- [`plan_implementacion.md`](docs/plan_implementacion.md)
---
 
## Variables de entorno
 
Cada componente tiene su propio `.env.example`, con los nombres de las variables y sin valores secretos. Los archivos `.env` no se versionan.
 
**Backend** (`backend/.env`)
 
| Variable | Uso |
|---|---|
| `DATABASE_URL` | Conexión a PostgreSQL |
| `SUPABASE_URL` | URL del proyecto de Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | Clave de servicio (Admin API para crear usuarios) |
| `SUPABASE_JWT_SECRET` | Validación del token en cada request |
| `CORS_ALLOWED_ORIGIN` | Único origen permitido (en local, `http://localhost:5173`) |
| `UMBRAL_VARIACION_DEFAULT_PCT` | Umbral global de variación inusual (por defecto `30.00`) |
| `TEST_DATABASE_URL` | Base descartable para pytest (host local y nombre terminado en `_test`) |
 
**Frontend** (`frontend/.env`)
 
| Variable | Uso |
|---|---|
| `VITE_API_URL` | URL del backend, sin barra final (en local, `http://localhost:8000`) |
| `VITE_SUPABASE_URL` | URL del proyecto de Supabase |
| `VITE_SUPABASE_ANON_KEY` | Clave pública (anon) de Supabase |
 
---
 
## Ejecución en local
 
Requisitos: Python 3.13, Node.js 22 y un proyecto de Supabase (o una base PostgreSQL con el esquema cargado).
 
**1. Base de datos**
Cargar `database/esquema_completo.sql` en la base de datos (y, opcionalmente, los datos de demostración de `database/seed`).
 
**2. Backend**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # completar los valores
uvicorn app.main:app --reload    # http://localhost:8000
```
 
**3. Frontend**
```bash
cd frontend
npm ci
cp .env.example .env             # completar los valores
npm run dev                      # http://localhost:5173
```
 
---
 
## Pruebas y contrato de la API
 
```bash
# Backend: los tests recrean el esquema en una base descartable (TEST_DATABASE_URL)
cd backend
python -m pytest
 
# Si cambia la API, regenerar el contrato y los tipos del frontend
python -m scripts.generar_openapi     # desde backend/ → actualiza docs/openapi.json
cd ../frontend
npm run gen:api                       # actualiza src/types/api.ts
 
# Frontend
npx tsc -b
npm run lint
```
 
El CI (`.github/workflows/ci.yml`) corre en cada pull request y en cada push a `main`. Falla si pytest no pasa, si `docs/openapi.json` o los archivos generados del frontend están desactualizados, o si fallan el build, el chequeo de tipos o el lint.
 
---
 
## Flujo de trabajo
 
- Ramas: `feat/<módulo>-<unidad>` o `chore/shared-<tema>`.
- Commits convencionales, en español.
- Un pull request por unidad de trabajo, revisado por el otro integrante antes del merge.
---
 
## Estado
 
El proyecto está en la **Fase 1 (desarrollo por módulos)**; la Fase 0 (fundación) está cerrada: esqueleto del repositorio, documentación del modelo, contrato de la API, CI y despliegue.
 
| Unidad | Alcance | Estado |
|---|---|---|
| A1 (HU-01) | Autenticación: endurecimiento del login, cierre de sesión, aviso por usuario inactivo o sesión vencida | Mergeado |
| B1 (HU-07) | Apertura de período y checklist mensual | Mergeado |
| B2 (HU-08) | Carga de importes con rechazo de duplicados y auditoría | Mergeado |
| A2 (HU-02) | Gestión de usuarios y roles | En curso |
| Resto de Fase 1 | Ver [`plan_implementacion.md`](docs/plan_implementacion.md) | Pendiente |
 
**Sistema desplegado**
 
- Backend (Render): https://tp-final-tupad-olima-pannunzio-4vnx.onrender.com
- Frontend (Vercel): https://tp-final-tupad-olima-pannunzio-tco7.vercel.app/
Este README se completa en la fase final con:
 
- el enlace al Informe Final y al video;
- la versión entregada (tag) y el detalle de lo implementado y lo proyectado.