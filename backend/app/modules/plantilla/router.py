from fastapi import APIRouter
from app.core.errors import no_implementado

router = APIRouter(prefix="/propiedades/{propiedad_id}/conceptos", tags=["plantilla"])


@router.get("")
def listar():
    raise no_implementado()