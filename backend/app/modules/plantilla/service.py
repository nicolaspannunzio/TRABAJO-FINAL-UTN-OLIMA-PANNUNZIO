"""HU-06: conceptos asociados a cada propiedad (RN-08). La plantilla alimenta el checklist."""
from uuid import UUID

from sqlmodel import Session

from app.core.errors import AppError
from app.modules.plantilla import repository
from app.modules.plantilla.schemas import (
    ConceptoPropiedadActualizar,
    ConceptoPropiedadCrear,
)


def _exigir_propiedad(session: Session, propiedad_id: UUID) -> None:
    if not repository.propiedad_existe(session, propiedad_id):
        raise AppError(404, "propiedad_no_encontrada", "La propiedad no existe",
                       {"propiedad_id": str(propiedad_id)})


def listar(session: Session, propiedad_id: UUID) -> list[dict]:
    _exigir_propiedad(session, propiedad_id)
    return repository.listar(session, propiedad_id)


def asociar(session: Session, propiedad_id: UUID, datos: ConceptoPropiedadCrear) -> dict:
    _exigir_propiedad(session, propiedad_id)
    if not repository.concepto_existe(session, datos.concepto_id):
        raise AppError(404, "concepto_no_encontrado", "El concepto no existe",
                       {"concepto_id": str(datos.concepto_id)})
    try:
        # Criterio 1 de HU-06: asociarlo otra vez se rechaza. Queda activo por defecto.
        return repository.crear(session, propiedad_id, datos.concepto_id)
    except repository.YaAsociado:
        raise AppError(409, "concepto_ya_asociado",
                       "El concepto ya está asociado a la propiedad",
                       {"propiedad_id": str(propiedad_id),
                        "concepto_id": str(datos.concepto_id)}) from None


def actualizar(session: Session, propiedad_id: UUID, concepto_propiedad_id: UUID,
               datos: ConceptoPropiedadActualizar) -> dict:
    fila = repository.cambiar_activo(session, propiedad_id, concepto_propiedad_id, datos.activo)
    if fila is None:
        raise AppError(404, "concepto_propiedad_no_encontrado",
                       "El concepto no está asociado a esa propiedad",
                       {"concepto_propiedad_id": str(concepto_propiedad_id)})
    return fila