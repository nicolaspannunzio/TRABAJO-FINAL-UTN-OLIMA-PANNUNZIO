from fastapi import APIRouter, Depends

from app.core.deps import Usuario, get_current_user

router = APIRouter(tags=["me"])


@router.get("/me", response_model=Usuario)
def me(user: Usuario = Depends(get_current_user)):
    return user