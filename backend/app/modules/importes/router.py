from fastapi import APIRouter
from app.core.errors import no_implementado

router = APIRouter(prefix="/importes", tags=["importes"])


@router.get("")
def listar():
    raise no_implementado()