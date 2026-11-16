from fastapi import APIRouter
from app.core.errors import no_implementado

router = APIRouter(prefix="/conceptos", tags=["conceptos"])


@router.get("")
def listar():
    raise no_implementado()