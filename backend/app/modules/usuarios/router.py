# modules/usuarios/router.py
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.contract import errores
from app.core.deps import require_admin
from app.core.errors import no_implementado
from app.modules.usuarios.schemas import UsuarioActualizar, UsuarioCrear, UsuarioOut

# Solo admin gestiona usuarios (requerimientos.md sección 9).
router = APIRouter(prefix="/usuarios", tags=["usuarios"],
                   dependencies=[Depends(require_admin)])


@router.get("", response_model=list[UsuarioOut])
def listar_usuarios():
    raise no_implementado()


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED,
             responses=errores(409, 500, 502))
def crear_usuario(datos: UsuarioCrear):
    raise no_implementado()


@router.patch("/{usuario_id}", response_model=UsuarioOut, responses=errores(404))
def actualizar_usuario(usuario_id: UUID, datos: UsuarioActualizar):
    raise no_implementado()


@router.post("/{usuario_id}/baja", response_model=UsuarioOut, responses=errores(404))
def dar_de_baja_usuario(usuario_id: UUID):
    raise no_implementado()