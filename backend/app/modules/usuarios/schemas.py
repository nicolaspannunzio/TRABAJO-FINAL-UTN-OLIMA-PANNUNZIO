# modules/usuarios/schemas.py
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

Rol = Literal["admin", "operador"]


class UsuarioOut(BaseModel):
    id: UUID
    nombre: str
    email: str
    rol: Rol
    activo: bool


class UsuarioCrear(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    nombre: str = Field(min_length=1)
    rol: Rol
    # Contraseña inicial que define el admin en el alta (decisión del equipo).
    # 6 es el mínimo por defecto de Supabase Auth.
    contrasena: str = Field(min_length=6)


class UsuarioActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=1)
    rol: Rol | None = None