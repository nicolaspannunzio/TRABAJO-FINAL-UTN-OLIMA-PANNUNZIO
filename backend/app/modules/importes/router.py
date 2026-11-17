# modules/importes/router.py
from uuid import UUID

from fastapi import APIRouter, status

from app.core.contract import errores
from app.core.errors import no_implementado
from app.modules.checklist.schemas import FilaChecklist
from app.modules.importes.schemas import ImporteCorregir, ImporteCrear, ImporteOut

router = APIRouter(prefix="/importes", tags=["importes"])


@router.post("", response_model=FilaChecklist, status_code=status.HTTP_201_CREATED,
             responses=errores(409))
def cargar_importe(datos: ImporteCrear):
    # HU-08: inserta el importe, pasa la fila a `cargado` y audita, en una transacción.
    # 409 si ya hay importe para el par (se conserva el primero);
    # 422 si el concepto no tiene fila en el checklist del período.
    raise no_implementado()


@router.patch("/{importe_id}", response_model=ImporteOut, responses=errores(404))
def corregir_importe(importe_id: UUID, datos: ImporteCorregir):
    raise no_implementado()