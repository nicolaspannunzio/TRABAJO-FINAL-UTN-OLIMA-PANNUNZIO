from fastapi import APIRouter
from app.core.errors import no_implementado

router = APIRouter(prefix="/advertencias", tags=["advertencias"])


@router.get("")
def listar():
    raise no_implementado()