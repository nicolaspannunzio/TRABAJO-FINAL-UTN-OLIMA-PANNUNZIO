from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import column, select, table
from sqlmodel import Session

from app.core.db import get_session
from app.core.errors import AppError
from app.core.security import decode_token

# Tablas del módulo `usuarios` (A): se leen con table()/column(), sin importar su código.
_usuario = table("usuario", column("id"), column("nombre"), column("email"),
                 column("activo"), column("rol_id"))
_rol = table("rol", column("id"), column("nombre"))

bearer = HTTPBearer(auto_error=False)  # auto_error=False: el 401 lo armamos nosotros


class Usuario(BaseModel):
    id: UUID
    nombre: str
    email: str
    rol: str
    activo: bool


def get_claims(cred: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    if cred is None:
        raise AppError(401, "no_autenticado", "Falta el token de autenticación")
    return decode_token(cred.credentials)


def get_current_user(claims: dict = Depends(get_claims),
                     session: Session = Depends(get_session)) -> Usuario:
    # get_claims va primero: sin token válido nunca se toca la base.
    try:
        user_id = UUID(claims["sub"])
    except (KeyError, ValueError):
        raise AppError(401, "token_invalido", "Token inválido")

    stmt = (
        select(_usuario.c.id, _usuario.c.nombre, _usuario.c.email,
               _usuario.c.activo, _rol.c.nombre.label("rol"))
        .select_from(_usuario.join(_rol, _rol.c.id == _usuario.c.rol_id))
        .where(_usuario.c.id == user_id)
    )
    row = session.connection().execute(stmt).mappings().first()

    if row is None:
        raise AppError(403, "usuario_no_registrado", "El usuario no está habilitado en el sistema")
    if not row["activo"]:
        raise AppError(403, "usuario_inactivo", "El usuario está inactivo")
    return Usuario(**row)


def require_admin(user: Usuario = Depends(get_current_user)) -> Usuario:
    if user.rol != "admin":
        raise AppError(403, "permiso_insuficiente", "Se requiere rol administrador")
    return user