from functools import lru_cache

import jwt
from jwt import PyJWKClient

from app.core.config import get_settings
from app.core.errors import AppError

AUDIENCE = "authenticated"


@lru_cache
def _jwks_client(supabase_url: str) -> PyJWKClient:
    return PyJWKClient(f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json")


def decode_token(token: str) -> dict:
    """Verifica firma, expiración y audiencia. Devuelve los claims o lanza 401."""
    s = get_settings()
    try:
        alg = jwt.get_unverified_header(token).get("alg")
        if alg == "HS256":
            if not s.supabase_jwt_secret:
                raise RuntimeError("Falta SUPABASE_JWT_SECRET para verificar tokens HS256")
            key, algorithms = s.supabase_jwt_secret, ["HS256"]
        elif alg in ("ES256", "RS256"):
            if not s.supabase_url:
                raise RuntimeError("Falta SUPABASE_URL para verificar tokens con JWKS")
            key = _jwks_client(s.supabase_url).get_signing_key_from_jwt(token).key
            algorithms = [alg]
        else:
            raise AppError(401, "token_invalido", "Token inválido")
        return jwt.decode(
            token, key, algorithms=algorithms, audience=AUDIENCE,
            options={"require": ["exp", "sub", "aud"]},
        )
    except jwt.ExpiredSignatureError:
        raise AppError(401, "token_expirado", "La sesión expiró")
    except jwt.PyJWTError:
        raise AppError(401, "token_invalido", "Token inválido")