# 🏠 Sistema de Asistencia para Liquidación de Alquileres

*Trabajo Final Integrador* — Tecnicatura Universitaria en Programación a Distancia (TUPAD)
Universidad Tecnológica Nacional · 2026

---

## 👥 Integrantes

| Rol | Nombre |
|---|---|
| Alumno | Olima, Nicolás |
| Alumno | Pannunzio, Nicolás |
| Tutor | Londero, Oscar |

---

## 📋 Sobre el proyecto

Herramienta web complementaria al sistema de gestión utilizado por una *inmobiliaria real*, pensada para asistir al personal administrativo durante el proceso mensual de liquidación de alquileres.

El sistema permite:
- 💰 Cargar los importes variables mensuales por propiedad (servicios, impuestos, seguros, etc.)
- ✅ Validar los datos para prevenir cargas duplicadas o inconsistentes
- 🤝 Calcular el reparto entre propietarios cuando existe tenencia compartida
- 📄 Generar el importe final listo para comunicar al inquilino

> No reemplaza al sistema de gestión existente — lo complementa, resolviendo específicamente la carga y validación de los importes variables mensuales.

---

## 🛠️ Tecnologías

| Componente | Stack |
|---|---|
| Frontend | TypeScript + React |
| Backend | Python + FastAPI |
| Base de datos | PostgreSQL (Supabase) |
| Autenticación | Supabase Auth |
| Comunicación | API REST (JSON) |
| Despliegue | Vercel (frontend) · Render (backend) |
| Control de versiones | Git + GitHub |

---

## 📁 Estructura del repositorio


/frontend    → Aplicación React
/backend     → API en FastAPI
/docs        → Documentación del proyecto