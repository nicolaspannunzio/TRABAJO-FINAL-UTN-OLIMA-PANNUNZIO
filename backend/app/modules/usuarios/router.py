from fastapi import APIRouter
from app.core.errors import no_implementado

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("")
def listar():
    raise no_implementado()