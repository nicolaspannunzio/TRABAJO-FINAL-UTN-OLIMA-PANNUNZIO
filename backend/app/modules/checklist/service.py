# modules/checklist/service.py
"""HU-07: apertura de período (RN-01, RN-09, RN-10).
HU-09: marcar un concepto como no corresponde (RN-10, RN-24, RN-25).

El formato AAAA-MM-01 ya lo valida el tipo Periodo del contrato (422 antes de llegar acá).
checklist e importes son los dos de B: se usa el repositorio de importes directamente.
"""
from datetime import date
from uuid import UUID

from sqlmodel import Session

from app import audit
from app.core.errors import AppError
from app.modules.checklist import repository
from app.modules.checklist.schemas import ChecklistOut, FilaChecklist, NoCorrespondeOut
from app.modules.importes import repository as importes_repo


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

def marcar_no_corresponde(session: Session, usuario_id: UUID, fila_id: UUID) -> NoCorrespondeOut:
    """Pasa la fila a no_corresponde (RN-25), desde pendiente o cargado.

    Si estaba cargado, en la misma transacción borra el importe y guarda en auditoría
    el valor anterior (importe, cargado_por, fecha_carga). Las preliquidaciones ya
    generadas no cambian: son snapshots con su propia copia del detalle.
    Si ya estaba en no_corresponde, responde igual sin cambios ni auditoría (idempotente).
    """
    fila = repository.fila_para_actualizar(session, fila_id)
    if fila is None:
        raise AppError(404, "fila_no_encontrada", "La fila del checklist no existe",
                       {"fila_id": str(fila_id)})

    estado_anterior = fila["estado"]
    if estado_anterior == "no_corresponde":
        session.rollback()  # libera el bloqueo: no hay nada que cambiar
        return NoCorrespondeOut(**repository.fila(session, fila_id),
                                estado_anterior=estado_anterior)

    importe = None
    if estado_anterior == "cargado":
        importe = importes_repo.buscar_para_borrar(session, fila["concepto_propiedad_id"],
                                                   fila["periodo"])
        if importe is not None:
            importes_repo.borrar(session, importe["id"])

    repository.cambiar_estado(session, fila_id, "no_corresponde")
    audit.registrar(session, usuario_id, "marcar_no_corresponde", "checklist_periodo", fila_id, {
        "propiedad_id": fila["propiedad_id"],
        "periodo": fila["periodo"],
        "concepto_propiedad_id": fila["concepto_propiedad_id"],
        "estado_anterior": estado_anterior,
        "importe_anterior": dict(importe) if importe is not None else None,
    })
    session.commit()

    return NoCorrespondeOut(**repository.fila(session, fila_id),
                            estado_anterior=estado_anterior,
                            importe_eliminado=importe["importe"] if importe is not None else None)
