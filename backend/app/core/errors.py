import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("app")


class AppError(Exception):
    def __init__(self, status: int, codigo: str, mensaje: str, detalle: dict | None = None):
        self.status, self.codigo, self.mensaje, self.detalle = status, codigo, mensaje, detalle or {}


def no_implementado() -> AppError:
    return AppError(501, "no_implementado", "Endpoint aún no implementado")


def _resp(status: int, codigo: str, mensaje: str, detalle: dict | None = None) -> JSONResponse:
    return JSONResponse(status_code=status,
                        content={"codigo": codigo, "mensaje": mensaje, "detalle": detalle or {}})


_CODIGOS_HTTP = {401: "no_autenticado", 403: "prohibido", 404: "no_encontrado", 409: "conflicto"}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, e: AppError):
        return _resp(e.status, e.codigo, e.mensaje, e.detalle)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, e: StarletteHTTPException):
        return _resp(e.status_code, _CODIGOS_HTTP.get(e.status_code, "error_http"), str(e.detail))

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, e: RequestValidationError):
        errores = [{"campo": ".".join(map(str, x["loc"])), "mensaje": x["msg"]} for x in e.errors()]
        return _resp(422, "validacion", "Datos de entrada inválidos", {"errores": errores})

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, e: Exception):
        log.exception("error no controlado")
        return _resp(500, "error_interno", "Error interno del servidor")