from fastapi import APIRouter
from app.core.errors import no_implementado

router = APIRouter(prefix="/preliquidaciones", tags=["preliquidaciones"])


@router.get("")
def listar():
    raise no_implementado()