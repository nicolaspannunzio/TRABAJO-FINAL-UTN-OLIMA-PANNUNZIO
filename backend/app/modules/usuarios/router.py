# modules/usuarios/router.py
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.contract import errores
from app.core.db import get_session
from app.core.deps import Usuario, require_admin
from app.modules.usuarios import service
from app.modules.usuarios.auth_admin import AuthAdmin, get_auth_admin
from app.modules.usuarios.schemas import UsuarioActualizar, UsuarioCrear, UsuarioOut

# Solo admin gestiona usuarios (requerimientos.md sección 9).
router = APIRouter(prefix="/usuarios", tags=["usuarios"],
                   dependencies=[Depends(require_admin)])


@router.get("", response_model=list[UsuarioOut])
def listar_usuarios(session: Session = Depends(get_session)):
    return service.listar(session)


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED,
             responses=errores(409, 500, 502))
def crear_usuario(datos: UsuarioCrear, session: Session = Depends(get_session),
                  auth_admin: AuthAdmin = Depends(get_auth_admin),
                  admin: Usuario = Depends(require_admin)):
    # HU-02: crea la cuenta en Supabase Auth y luego la fila en `usuario` con el mismo id.
    # 409 email repetido; 502 si falla la Admin API (no se crea nada);
    # 500 si falla el insert (se borra la cuenta de Auth para compensar).
    return service.crear_usuario(session, auth_admin, admin.id, datos)


@router.patch("/{usuario_id}", response_model=UsuarioOut, responses=errores(404))
def actualizar_usuario(usuario_id: UUID, datos: UsuarioActualizar,
                       session: Session = Depends(get_session),
                       admin: Usuario = Depends(require_admin)):
    return service.actualizar_usuario(session, admin.id, usuario_id, datos)


@router.post("/{usuario_id}/baja", response_model=UsuarioOut, responses=errores(404))
def dar_de_baja_usuario(usuario_id: UUID, session: Session = Depends(get_session),
                        admin: Usuario = Depends(require_admin)):
    # Baja lógica (RN-03): activo = false, la fila no se borra. Queda en auditoría.
    return service.dar_de_baja(session, admin.id, usuario_id)
