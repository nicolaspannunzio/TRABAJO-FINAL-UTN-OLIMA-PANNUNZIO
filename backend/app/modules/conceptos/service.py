# modules/conceptos/service.py
"""HU-05: catálogo de conceptos con umbral de variación opcional (RN-07)."""
from uuid import UUID

from sqlmodel import Session

from app.core.errors import AppError
from app.modules.conceptos import repository
from app.modules.conceptos.models import Concepto
from app.modules.conceptos.schemas import ConceptoActualizar, ConceptoCrear


def _no_encontrado(concepto_id: UUID) -> AppError:
    return AppError(404, "concepto_no_encontrado", "El concepto no existe",
                    {"concepto_id": str(concepto_id)})


def _nombre_duplicado(nombre: str) -> AppError:
    return AppError(409, "concepto_duplicado", "Ya existe un concepto con ese nombre",
                    {"nombre": nombre})


def listar(session: Session) -> list[Concepto]:
    return repository.listar(session)


def crear(session: Session, datos: ConceptoCrear) -> Concepto:
    # Criterio 2: sin umbral queda NULL (usa el umbral global).
    try:
        return repository.crear(session, datos.model_dump())
    except repository.NombreDuplicado:
        raise _nombre_duplicado(datos.nombre) from None


def actualizar(session: Session, concepto_id: UUID, datos: ConceptoActualizar) -> Concepto:
    concepto = repository.obtener(session, concepto_id)
    if concepto is None:
        raise _no_encontrado(concepto_id)
    # exclude_unset: solo se tocan los campos que vinieron en el PATCH.
    # Un umbral enviado como null explícito vuelve a "usar el global".
    cambios = datos.model_dump(exclude_unset=True)
    try:
        return repository.actualizar(session, concepto, cambios)
    except repository.NombreDuplicado:
        raise _nombre_duplicado(cambios.get("nombre", concepto.nombre)) from None