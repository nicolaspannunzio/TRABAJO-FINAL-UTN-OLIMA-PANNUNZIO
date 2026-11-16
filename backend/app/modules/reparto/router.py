from fastapi import APIRouter
from app.core.errors import no_implementado

router = APIRouter(prefix="/propiedades/{propiedad_id}/propietarios", tags=["reparto"])


@router.get("")
def listar():
    raise no_implementado()