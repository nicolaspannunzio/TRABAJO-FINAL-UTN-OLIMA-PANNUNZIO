from fastapi import APIRouter
from app.core.errors import no_implementado

router = APIRouter(prefix="/propiedades", tags=["propiedades"])


@router.get("")
def listar():
    raise no_implementado()