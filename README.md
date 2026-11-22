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
 
## Sistema desplegado y entregables
 
| Qué | Enlace |
|---|---|
| Frontend (Vercel) | https://tp-final-tupad-olima-pannunzio-tco7.vercel.app/ |
| Backend (Render) | https://tp-final-tupad-olima-pannunzio-4vnx.onrender.com (estado: [`/health`](https://tp-final-tupad-olima-pannunzio-4vnx.onrender.com/health)) |
| Base de datos y Auth (Supabase) | Proyecto privado del equipo: el panel de Supabase solo abre para los integrantes (ver [Verificación por un tercero](#verificación-por-un-tercero), nota C) |
| Informe Final (PDF) | [docs/Trabajo_Final_TUPaD_Informe.pdf](/docs/Trabajo_Final_TUPaD_Informe.pdf) |
| Video de presentación | https://drive.google.com/drive/folders/1CaJsjOmDJUGX8u9oB0WoJePpDgt-MdoV?usp=drive_link |
 
**Cuenta demo (rol operador):** `operador@emailprueba.com` / `2026tupad+`. Es una cuenta de prueba con datos ficticios: permite recorrer el sistema completo salvo la gestión de usuarios, que es exclusiva del rol administrador. La cuenta de administrador se entrega al tutor por mensaje privado. En este repositorio no hay credenciales reales.
 
> **Aviso de arranque en frío.** El backend en Render se duerme cuando no tiene tráfico y la primera petición puede tardar hasta cerca de un minuto. Antes de usar el sistema o de mostrarlo, abrí `/health` en el navegador y esperá a que responda; después el frontend anda con normalidad.
 
**Versión entregada:** tag v1.0.1. Los tres componentes desplegados corresponden al commit de ese tag.
 
---
 
## Verificación por un tercero
 
Hay dos formas de comprobar que el sistema funciona sin depender de los integrantes.
 
**A. Sin instalar nada (sistema desplegado)**
 
1. Abrir [`/health`](https://tp-final-tupad-olima-pannunzio-4vnx.onrender.com/health) y esperar `{"estado":"ok","base":"ok"}` (por el arranque en frío puede tardar cerca de un minuto).
2. Abrir el [frontend](https://tp-final-tupad-olima-pannunzio-tco7.vercel.app/) e iniciar sesión con la cuenta demo.
3. Seguir el recorrido de demostración: pasos 1 a 13 del guion en [`plan_implementacion.md`](docs/plan_implementacion.md), sección 6. El paso 14 (alta o baja de un usuario) necesita la cuenta de administrador. Las capturas de cada paso están en [`docs/evidencia`](docs/evidencia).
 
**B. Solo las pruebas automáticas, en local (no necesita Supabase)**
 
Requisitos: Python 3.13 y PostgreSQL. Seguir el paso **2. Backend** de [Ejecución en local](#ejecución-en-local) hasta `cp .env.example .env` y después [Pruebas y contrato de la API](#pruebas-y-contrato-de-la-api). Solo hace falta completar `TEST_DATABASE_URL`. Resultado esperado: `338 passed`.
 
Este camino se verificó el 20/11/2026 sobre un clon limpio del repositorio, siguiendo únicamente este README.
 
> **C. Nota sobre el sistema completo en local.** La base de datos de la aplicación y el inicio de sesión corren en un proyecto de Supabase que es privado del equipo: su panel solo abre para los integrantes y sus claves no se publican. Por eso no se comparte. Para levantar el sistema completo en otra máquina hace falta un proyecto de Supabase propio (el plan gratuito alcanza), siguiendo [Ejecución en local](#ejecución-en-local) desde el paso 1.
 
---
 
## Qué está implementado y qué es proyectado
 
Las 14 historias de usuario (HU-01 a HU-14) están implementadas, desplegadas y probadas: A1–A6 y B1–B9, con su recorrido de demo (14 pasos) y las capturas en [`docs/evidencia`](docs/evidencia). El detalle por historia, con rutas, pruebas y evidencia, está en [`docs/implementado_vs_proyectado.md`](docs/implementado_vs_proyectado.md); la matriz de pruebas por criterio de aceptación, en [`docs/pruebas.md`](docs/pruebas.md).
 
Lo proyectado (no construido) es el fuera de alcance de arriba: contratos e inquilinos, alertas de vencimiento y emails. Las reglas con la inmobiliaria que quedan **a confirmar** (umbral de variación de 30 % y bloqueo al generar con conceptos pendientes) están implementadas como configurables.
 
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
/database    → Esquema (esquema_completo.sql), migraciones y seed (seed_demo.sql, reset_demo.sql)
/docs        → Documentación del proyecto, contrato de la API (openapi.json) y evidencia
/.github     → Workflow de CI
```
 
La documentación está en [`/docs`](docs):
 
- [`requerimientos.md`](docs/requerimientos.md): problema, alcance, historias de usuario y reglas de negocio
- [`arquitectura.md`](docs/arquitectura.md)
- [`diagrama_ER.md`](docs/diagrama_ER.md)
- [`listado_modulos.md`](docs/listado_modulos.md)
- [`plan_implementacion.md`](docs/plan_implementacion.md): unidades de trabajo y guion de la demo
- [`pruebas.md`](docs/pruebas.md)
- [`implementado_vs_proyectado.md`](docs/implementado_vs_proyectado.md)
---
 
## Variables de entorno
 
Cada componente tiene su propio `.env.example`, con los nombres de las variables y sin valores secretos. Los archivos `.env` no se versionan. En producción las variables del backend se definen en Render y las del frontend en Vercel.
 
**Backend** (`backend/.env` en local, Render en producción)
 
| Variable | Uso |
|---|---|
| `DATABASE_URL` | Conexión a PostgreSQL |
| `SUPABASE_URL` | URL del proyecto de Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | Clave de servicio (Admin API para crear usuarios) |
| `SUPABASE_JWT_SECRET` | Validación del token en cada request |
| `CORS_ALLOWED_ORIGIN` | Único origen permitido (en local, `http://localhost:5173`; en Render, la URL de Vercel) |
| `UMBRAL_VARIACION_DEFAULT_PCT` | Umbral global de variación inusual (por defecto `30.00`) |
| `TEST_DATABASE_URL` | Base descartable para pytest (host local y nombre terminado en `_test`) |
 
**Frontend** (`frontend/.env` en local, Vercel en producción)
 
| Variable | Uso |
|---|---|
| `VITE_API_URL` | URL del backend, sin barra final (en local, `http://localhost:8000`) |
| `VITE_SUPABASE_URL` | URL del proyecto de Supabase |
| `VITE_SUPABASE_ANON_KEY` | Clave pública (anon) de Supabase |
 
---
 
## Ejecución en local
 
Requisitos: Python 3.13, Node.js 22, PostgreSQL local (para las pruebas) y un proyecto de Supabase (para Auth y la base de la aplicación).
 
**1. Base de datos**
 
1. En el proyecto de Supabase, cargar `database/esquema_completo.sql` (SQL Editor).
2. Aplicar las migraciones de `database/migrations/` en orden. En una base nueva no cambian nada, porque `esquema_completo.sql` ya las incluye, pero se pueden ejecutar igual sin error. Hacen falta en una base creada con una versión anterior del esquema.
3. Crear un usuario en Supabase Auth (Authentication → Users) y una fila en la tabla `usuario` con **el mismo id** y rol `admin`. Con ese usuario se inicia sesión.
4. Opcional, para tener datos de demostración: ejecutar `database/seed/seed_demo.sql`. Necesita ese usuario `admin` y una base limpia. Para volver a cargarla en un ensayo, ejecutar antes `database/seed/reset_demo.sql` (solo para ensayos: deshabilita los triggers de inmutabilidad).
**2. Backend**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # completar los valores
uvicorn app.main:app --reload    # http://localhost:8000  (estado: /health)
```
 
**3. Frontend**
```bash
cd frontend
npm ci
cp .env.example .env             # completar los valores
npm run dev                      # http://localhost:5173
```
 
Con los dos servidores levantados, abrir http://localhost:5173 e iniciar sesión con el usuario del paso 1.3.
 
---
 
## Pruebas y contrato de la API
 
Los tests del backend recrean el esquema en una base PostgreSQL local y descartable. Antes de correrlos, crear la base (por ejemplo `createdb preliquidacion_test`) y definir `TEST_DATABASE_URL` en `backend/.env` apuntando a ella; si el host no es local o el nombre no termina en `_test`, pytest aborta para no tocar datos reales.
 
```bash
# Backend
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
 
- Ramas: `feat/<módulo>-<unidad>`, `fix/<módulo>-<tema>`, `docs/<tema>` o `chore/shared-<tema>`.
- Commits convencionales, en español.
- Un pull request por unidad de trabajo, revisado por el otro integrante antes del merge.
 