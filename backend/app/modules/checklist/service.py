# modules/checklist/service.py
"""HU-07: apertura de período (RN-01, RN-09, RN-10).

El formato AAAA-MM-01 ya lo valida el tipo Periodo del contrato (422 antes de llegar acá).
"""
from datetime import date
from uuid import UUID

from sqlmodel import Session

from app.core.errors import AppError
from app.modules.checklist import repository
from app.modules.checklist.schemas import ChecklistOut, FilaChecklist


def _armar(session: Session, propiedad_id: UUID, periodo: date) -> ChecklistOut:
    filas = [FilaChecklist(**f) for f in repository.filas(session, propiedad_id, periodo)]
    return ChecklistOut(propiedad_id=propiedad_id, periodo=periodo, filas=filas)


def abrir_periodo(session: Session, propiedad_id: UUID, periodo: date) -> tuple[ChecklistOut, bool]:
    """Devuelve (checklist, creado). Idempotente: si el período ya está abierto
    devuelve el existente sin agregar filas (creado=False)."""
    if not repository.propiedad_existe(session, propiedad_id):
        raise AppError(404, "propiedad_no_encontrada", "La propiedad no existe",
                       {"propiedad_id": str(propiedad_id)})

    if repository.checklist_existe(session, propiedad_id, periodo):
        return _armar(session, propiedad_id, periodo), False

    activos = repository.conceptos_activos(session, propiedad_id)
    repository.insertar_filas(session, propiedad_id, periodo, activos)
    session.commit()
    return _armar(session, propiedad_id, periodo), True


def obtener_checklist(session: Session, propiedad_id: UUID, periodo: date) -> ChecklistOut:
    checklist = _armar(session, propiedad_id, periodo)
    if not checklist.filas:
        raise AppError(404, "checklist_no_encontrado",
                       "El período no está abierto para esa propiedad",
                       {"propiedad_id": str(propiedad_id), "periodo": periodo.isoformat()})
    return checklist