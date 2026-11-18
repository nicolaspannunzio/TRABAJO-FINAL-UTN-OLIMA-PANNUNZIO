# modules/usuarios/repository.py
from uuid import UUID

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.modules.usuarios.models import Rol, Usuario

_usuario = Usuario.__table__
_rol = Rol.__table__

# UNIQUE de usuario.email en esquema_completo.sql (nombre que Postgres le da por defecto).
_UQ_EMAIL = "usuario_email_key"


class EmailDuplicado(Exception):
    """Ya existe un usuario con ese email."""


def _consulta_base():
    return (
        select(_usuario.c.id, _usuario.c.nombre, _usuario.c.email,
               _rol.c.nombre.label("rol"), _usuario.c.activo)
        .select_from(_usuario.join(_rol, _rol.c.id == _usuario.c.rol_id))
    )


def listar(session: Session) -> list[dict]:
    stmt = _consulta_base().order_by(_usuario.c.nombre, _usuario.c.email)
    return [dict(f) for f in session.connection().execute(stmt).mappings().all()]


def obtener(session: Session, usuario_id: UUID) -> dict | None:
    stmt = _consulta_base().where(_usuario.c.id == usuario_id)
    fila = session.connection().execute(stmt).mappings().first()
    return dict(fila) if fila else None


def id_del_rol(session: Session, nombre: str) -> UUID:
    """Los roles 'admin' y 'operador' los siembra el script SQL; el schema ya validó el nombre."""
    stmt = select(_rol.c.id).where(_rol.c.nombre == nombre)
    return session.connection().execute(stmt).scalar_one()


def insertar(session: Session, usuario_id: UUID, nombre: str, email: str, rol_id: UUID) -> None:
    """Inserta la fila con el id que devolvió Supabase Auth. No confirma: lo hace el service.

    El email repetido se detecta por la restricción de la base, no con una consulta previa
    (convención 7): así también se cubren dos altas simultáneas.
    """
    stmt = insert(_usuario).values(id=usuario_id, nombre=nombre, email=email, rol_id=rol_id)
    try:
        session.connection().execute(stmt)
    except IntegrityError as e:
        diag = getattr(e.orig, "diag", None)
        if getattr(diag, "constraint_name", None) == _UQ_EMAIL:
            raise EmailDuplicado from e
        raise


def actualizar(session: Session, usuario_id: UUID, cambios: dict) -> None:
    """`cambios` trae solo las columnas a modificar (nombre y/o rol_id)."""
    session.connection().execute(
        update(_usuario).where(_usuario.c.id == usuario_id).values(**cambios))


def marcar_inactivo(session: Session, usuario_id: UUID) -> None:
    session.connection().execute(
        update(_usuario).where(_usuario.c.id == usuario_id).values(activo=False))
