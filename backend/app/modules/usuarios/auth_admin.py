# modules/usuarios/auth_admin.py
"""Cliente mínimo de la Admin API de Supabase Auth (crear y borrar cuentas).

Usa la clave `service_role`, que existe solo como variable de entorno en Render (RN-04).
Nunca se loguea ni se devuelve el cuerpo del pedido: lleva la contraseña inicial.
"""
from uuid import UUID

import httpx

from app.core.config import get_settings
from app.core.errors import AppError


class AuthAdminError(Exception):
    """Falló la Admin API. `codigo` es el `error_code` de Supabase, si lo informó."""

    def __init__(self, mensaje: str, codigo: str | None = None):
        super().__init__(mensaje)
        self.codigo = codigo


class AuthAdmin:
    def __init__(self, supabase_url: str, service_role_key: str, timeout: float = 10.0):
        self._base = f"{supabase_url.rstrip('/')}/auth/v1/admin/users"
        self._headers = {"apikey": service_role_key,
                         "Authorization": f"Bearer {service_role_key}"}
        self._timeout = timeout

    def _pedir(self, metodo: str, url: str, **kwargs) -> httpx.Response:
        try:
            return httpx.request(metodo, url, headers=self._headers,
                                 timeout=self._timeout, **kwargs)
        except httpx.HTTPError as e:
            raise AuthAdminError("No se pudo conectar con Supabase Auth") from e

    @staticmethod
    def _error(r: httpx.Response) -> AuthAdminError:
        try:
            codigo = r.json().get("error_code")
        except ValueError:  # el cuerpo no era JSON
            codigo = None
        return AuthAdminError(f"Supabase Auth respondió {r.status_code}", codigo)

    def crear_usuario(self, email: str, contrasena: str) -> UUID:
        """Crea la cuenta (ya confirmada, sin mail de verificación) y devuelve su id."""
        r = self._pedir("POST", self._base,
                        json={"email": email, "password": contrasena, "email_confirm": True})
        if r.status_code >= 400:
            raise self._error(r)
        return UUID(r.json()["id"])

    def eliminar_usuario(self, usuario_id: UUID) -> None:
        """Borra la cuenta. Que ya no exista (404) cuenta como éxito."""
        r = self._pedir("DELETE", f"{self._base}/{usuario_id}")
        if r.status_code >= 400 and r.status_code != 404:
            raise self._error(r)


def get_auth_admin() -> AuthAdmin:
    """Dependencia FastAPI. Los tests la reemplazan con dependency_overrides."""
    s = get_settings()
    if not s.supabase_url or not s.supabase_service_role_key:
        raise AppError(502, "auth_error",
                       "Falta configurar SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en el backend")
    return AuthAdmin(s.supabase_url, s.supabase_service_role_key)
