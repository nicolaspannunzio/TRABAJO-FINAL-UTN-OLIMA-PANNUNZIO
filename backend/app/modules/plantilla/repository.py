from uuid import UUID

from sqlalchemy import column, table
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.modules.plantilla.models import ConceptoPropiedad

# Tablas de otros módulos: solo se leen, con table()/column() (convención 2).
_concepto = table("concepto", column("id"), column("nombre"))
_propiedad = table("propiedad", column("id"))

# UNIQUE (propiedad_id, concepto_id) en esquema_completo.sql (nombre por defecto de Postgres).
_UQ_ASOCIACION = "concepto_propiedad_propiedad_id_concepto_id_key"


class YaAsociado(Exception):
    """El concepto ya está asociado a la propiedad."""


def _consulta():
    return (
        select(ConceptoPropiedad.id, ConceptoPropiedad.propiedad_id,
               ConceptoPropiedad.concepto_id, _concepto.c.nombre, ConceptoPropiedad.activo)
        .join(_concepto, _concepto.c.id == ConceptoPropiedad.concepto_id)
    )


def _a_dict(fila) -> dict:
    i, propiedad_id, concepto_id, nombre, activo = fila
    return {"id": i, "propiedad_id": propiedad_id, "concepto_id": concepto_id,
            "concepto": nombre, "activo": activo}


def propiedad_existe(session: Session, propiedad_id: UUID) -> bool:
    return session.exec(select(_propiedad.c.id).where(_propiedad.c.id == propiedad_id)).first() is not None


def concepto_existe(session: Session, concepto_id: UUID) -> bool:
    return session.exec(select(_concepto.c.id).where(_concepto.c.id == concepto_id)).first() is not None


def listar(session: Session, propiedad_id: UUID) -> list[dict]:
    filas = session.exec(
        _consulta().where(ConceptoPropiedad.propiedad_id == propiedad_id)
        .order_by(_concepto.c.nombre, ConceptoPropiedad.id)
    ).all()
    return [_a_dict(f) for f in filas]


def obtener(session: Session, propiedad_id: UUID, concepto_propiedad_id: UUID) -> dict | None:
    fila = session.exec(
        _consulta().where(ConceptoPropiedad.id == concepto_propiedad_id,
                          ConceptoPropiedad.propiedad_id == propiedad_id)
    ).first()
    return _a_dict(fila) if fila else None


def crear(session: Session, propiedad_id: UUID, concepto_id: UUID) -> dict:
    """COMMIT. El duplicado se detecta por la restricción de la base (convención 7), no con
    una consulta previa: así también se cubren dos asociaciones simultáneas."""
    asociacion = ConceptoPropiedad(propiedad_id=propiedad_id, concepto_id=concepto_id)
    session.add(asociacion)
    try:
        session.commit()
    except IntegrityError as e:
        session.rollback()
        diag = getattr(e.orig, "diag", None)
        if getattr(diag, "constraint_name", None) == _UQ_ASOCIACION:
            raise YaAsociado from e
        raise
    session.refresh(asociacion)  # trae el id que puso la base
    return obtener(session, propiedad_id, asociacion.id)


def cambiar_activo(session: Session, propiedad_id: UUID, concepto_propiedad_id: UUID,
                   activo: bool) -> dict | None:
    # Se filtra también por propiedad: un id de otra propiedad no existe para esta ruta.
    asociacion = session.exec(
        select(ConceptoPropiedad).where(ConceptoPropiedad.id == concepto_propiedad_id,
                                        ConceptoPropiedad.propiedad_id == propiedad_id)
    ).first()
    if asociacion is None:
        return None
    asociacion.activo = activo
    session.add(asociacion)
    session.commit()
    return obtener(session, propiedad_id, concepto_propiedad_id)