# modules/usuarios/service.py
"""HU-02: gestión de usuarios (RN-02, RN-03, RN-24). Solo `admin` (lo exige el router).

El alta toca dos sistemas (Supabase Auth y nuestra base), que no comparten transacción:
primero se crea la cuenta en Auth y después la fila en `usuario`. Si lo segundo falla,
se borra la cuenta recién creada para no dejar cuentas huérfanas (compensación).
"""
import logging
from uuid import UUID

from sqlmodel import Session

from app import audit
from app.core.errors import AppError
from app.modules.usuarios import repository
from app.modules.usuarios.auth_admin import AuthAdmin, AuthAdminError
from app.modules.usuarios.schemas import UsuarioActualizar, UsuarioCrear, UsuarioOut

log = logging.getLogger("app")


def _no_encontrado(usuario_id: UUID) -> AppError:
    return AppError(404, "usuario_no_encontrado", "El usuario no existe",
                    {"usuario_id": str(usuario_id)})


def _email_duplicado(email: str) -> AppError:
    return AppError(409, "email_duplicado", "Ya existe un usuario con ese email",
                    {"email": email})


def listar(session: Session) -> list[UsuarioOut]:
    return [UsuarioOut(**f) for f in repository.listar(session)]


def crear_usuario(session: Session, auth_admin: AuthAdmin, admin_id: UUID,
                  datos: UsuarioCrear) -> UsuarioOut:
    # Supabase guarda el email en minúsculas; hacemos lo mismo para que ambos coincidan.
    email = datos.email.strip().lower()
    rol_id = repository.id_del_rol(session, datos.rol)

    # 1) Cuenta en Auth. Si falla, no se creó nada y no hay nada que compensar.
    try:
        usuario_id = auth_admin.crear_usuario(email, datos.contrasena)
    except AuthAdminError as e:
        if e.codigo == "email_exists":
            raise _email_duplicado(email)
        if e.codigo == "weak_password":
            raise AppError(422, "contrasena_invalida",
                           "La contraseña no cumple los requisitos de Supabase Auth")
        log.error("Falló la Admin API al crear una cuenta: %s", e)  # sin la contraseña
        raise AppError(502, "auth_error", "No se pudo crear la cuenta en Supabase Auth")

    # 2) Fila en `usuario` y auditoría, en una transacción. La contraseña no se guarda
    #    en `usuario`, ni en `auditoria`, ni en los logs.
    try:
        repository.insertar(session, usuario_id, datos.nombre, email, rol_id)
        audit.registrar(session, admin_id, "alta_usuario", "usuario", usuario_id, {
            "email": email, "nombre": datos.nombre, "rol": datos.rol})
        session.commit()
    except Exception as e:
        session.rollback()
        _compensar(auth_admin, usuario_id)
        if isinstance(e, repository.EmailDuplicado):
            raise _email_duplicado(email)
        log.exception("Falló el alta en la base; se compensó la cuenta de Auth")
        raise AppError(500, "error_interno", "Error interno del servidor")

    return UsuarioOut(**repository.obtener(session, usuario_id))


def _compensar(auth_admin: AuthAdmin, usuario_id: UUID) -> None:
    """Borra la cuenta de Auth. Si tampoco se puede, queda un id huérfano: se loguea
    y se documenta como limitación (decisión del equipo, requerimientos.md sección 9)."""
    try:
        auth_admin.eliminar_usuario(usuario_id)
    except Exception:
        log.error("Cuenta huérfana en Supabase Auth, borrarla a mano: %s", usuario_id)


def actualizar_usuario(session: Session, admin_id: UUID, usuario_id: UUID,
                       datos: UsuarioActualizar) -> UsuarioOut:
    actual = repository.obtener(session, usuario_id)
    if actual is None:
        raise _no_encontrado(usuario_id)

    # Solo cambia lo que vino en el body y difiere de lo guardado.
    cambios, antes, despues = {}, {}, {}
    if datos.nombre is not None and datos.nombre != actual["nombre"]:
        cambios["nombre"] = datos.nombre
        antes["nombre"], despues["nombre"] = actual["nombre"], datos.nombre
    if datos.rol is not None and datos.rol != actual["rol"]:
        cambios["rol_id"] = repository.id_del_rol(session, datos.rol)
        antes["rol"], despues["rol"] = actual["rol"], datos.rol

    if cambios:
        repository.actualizar(session, usuario_id, cambios)
        audit.registrar(session, admin_id, "edicion_usuario", "usuario", usuario_id,
                        {"antes": antes, "despues": despues})
        session.commit()
    return UsuarioOut(**repository.obtener(session, usuario_id))


def dar_de_baja(session: Session, admin_id: UUID, usuario_id: UUID) -> UsuarioOut:
    """Baja lógica (RN-03): `activo = false`, la fila no se borra. Idempotente: si ya
    estaba inactivo responde 200 sin cambios ni auditoría."""
    actual = repository.obtener(session, usuario_id)
    if actual is None:
        raise _no_encontrado(usuario_id)

    if actual["activo"]:
        repository.marcar_inactivo(session, usuario_id)
        audit.registrar(session, admin_id, "baja_usuario", "usuario", usuario_id,
                        {"email": actual["email"], "rol": actual["rol"]})
        session.commit()
    return UsuarioOut(**repository.obtener(session, usuario_id))
