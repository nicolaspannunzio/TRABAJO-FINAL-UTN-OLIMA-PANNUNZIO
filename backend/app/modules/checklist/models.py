# modules/checklist/models.py
"""Tablas que posee el módulo checklist (plan_implementacion.md, sección 2): checklist_periodo.

El esquema sale de database/esquema_completo.sql (no se usa create_all()).
propiedad_id y concepto_propiedad_id apuntan a tablas de A (propiedades y plantilla):
se declaran SIN foreign_key= (convención 3); la base hace cumplir las FK por el DDL.
"""
from datetime import date
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ChecklistPeriodo(SQLModel, table=True):
    __tablename__ = "checklist_periodo"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    propiedad_id: UUID
    periodo: date  # siempre AAAA-MM-01 (RN-01; CHECK ck_checklist_periodo_primer_dia)
    concepto_propiedad_id: UUID
    estado: str = Field(default="pendiente")  # pendiente | cargado | no_corresponde