# modules/conceptos/repository.py
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.modules.conceptos.models import Concepto

# Índice único de concepto.nombre (sin distinguir mayúsculas) en esquema_completo.sql.
_UQ_NOMBRE = "uq_concepto_nombre_ci"


class NombreDuplicado(Exception):
    """Ya existe un concepto con ese nombre."""


def _confirmar(session: Session) -> None:
    """COMMIT. El nombre repetido se detecta por la restricción de la base, no con una
    consulta previa (convención 7): así también se cubren dos altas simultáneas."""
    try:
        session.commit()
    except IntegrityError as e:
        session.rollback()
        diag = getattr(e.orig, "diag", None)
        if getattr(diag, "constraint_name", None) == _UQ_NOMBRE:
            raise NombreDuplicado from e
        raise


def listar(session: Session) -> list[Concepto]:
    return list(session.exec(select(Concepto).order_by(Concepto.nombre)).all())


def obtener(session: Session, concepto_id: UUID) -> Concepto | None:
    return session.get(Concepto, concepto_id)


def crear(session: Session, datos: dict) -> Concepto:
    concepto = Concepto(**datos)
    session.add(concepto)
    _confirmar(session)
    session.refresh(concepto)  # trae el id que puso la base
    return concepto


def actualizar(session: Session, concepto: Concepto, cambios: dict) -> Concepto:
    for campo, valor in cambios.items():
        setattr(concepto, campo, valor)
    session.add(concepto)
    _confirmar(session)
    session.refresh(concepto)
    return concepto
