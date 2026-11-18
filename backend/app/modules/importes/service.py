# modules/importes/service.py
"""HU-08: carga de importes (RN-10, RN-11, RN-12, RN-13, RN-24).

importes y checklist son los dos de B: se usa el repositorio del checklist directamente
(la regla de no importar código aplica entre módulos de distinto integrante).
"""
from uuid import UUID

from sqlmodel import Session

from app import audit
from app.core.errors import AppError
from app.modules.checklist import repository as checklist_repo
from app.modules.checklist.schemas import FilaChecklist
from app.modules.importes import repository
from app.modules.importes.schemas import ImporteCrear


def cargar_importe(session: Session, usuario_id: UUID, datos: ImporteCrear) -> FilaChecklist:
    """Inserta el importe, pasa la fila del checklist a `cargado` y audita.

    Todo en una transacción: si algo falla, no queda ni el importe ni el cambio de estado.
    """
    fila = checklist_repo.fila_por_concepto(session, datos.propiedad_id, datos.periodo,
                                            datos.concepto_propiedad_id)
    if fila is None:
        # Criterio 4 de HU-08: período sin abrir, concepto inactivo o de otra propiedad.
        raise AppError(422, "concepto_sin_fila_checklist",
                       "El concepto no tiene fila en el checklist de ese período",
                       {"propiedad_id": str(datos.propiedad_id),
                        "periodo": datos.periodo.isoformat(),
                        "concepto_propiedad_id": str(datos.concepto_propiedad_id)})

    try:
        importe_id = repository.insertar(session, datos.concepto_propiedad_id, datos.periodo,
                                         datos.importe, usuario_id)
    except repository.ImporteDuplicado:
        session.rollback()  # la transacción quedó abortada por el IntegrityError
        raise AppError(409, "importe_duplicado",
                       "Ya hay un importe cargado para este concepto en el período; "
                       "se conserva el primero",
                       {"concepto_propiedad_id": str(datos.concepto_propiedad_id),
                        "periodo": datos.periodo.isoformat()})

    checklist_repo.cambiar_estado(session, fila["id"], "cargado")
    audit.registrar(session, usuario_id, "carga_importe", "importe_mensual", importe_id, {
        "propiedad_id": datos.propiedad_id,
        "periodo": datos.periodo,
        "concepto_propiedad_id": datos.concepto_propiedad_id,
        "checklist_id": fila["id"],
        "importe": datos.importe,
        "estado_anterior": fila["estado"],
    })
    session.commit()

    return FilaChecklist(**checklist_repo.fila(session, fila["id"]))
