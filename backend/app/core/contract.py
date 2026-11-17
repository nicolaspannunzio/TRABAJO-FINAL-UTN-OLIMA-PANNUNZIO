"""Piezas comunes del contrato de API (plan_implementacion.md, sección 4).

- ErrorRespuesta: cuerpo único de error {codigo, mensaje, detalle}.
- errores(...): respuestas de error para declarar en `responses=` de cada ruta.
- Importe, Porcentaje, UmbralPct: Decimal que viaja como cadena ("15000.00"), nunca float.
- Periodo: fecha que debe ser el primer día del mes (AAAA-MM-01). Se rechaza, no se normaliza.
"""
from datetime import date
from decimal import Decimal
from typing import Annotated, Any

from pydantic import (AfterValidator, BaseModel, BeforeValidator, Field,
                      PlainSerializer, WithJsonSchema)


class ErrorRespuesta(BaseModel):
    codigo: str
    mensaje: str
    detalle: dict[str, Any] = Field(default_factory=dict)


_DESCRIPCIONES = {
    401: "Sin token o token inválido",
    403: "Usuario inactivo o sin permiso",
    404: "El recurso no existe",
    409: "Conflicto con el estado actual",
    422: "Datos de entrada inválidos",
    500: "Error interno",
    502: "Falla de una dependencia externa",
}


def errores(*codigos: int) -> dict[int | str, dict[str, Any]]:
    """Respuestas de error con el formato del contrato, para `responses=`."""
    return {c: {"model": ErrorRespuesta, "description": _DESCRIPCIONES[c]} for c in codigos}


# --- Dinero y porcentajes: cadenas decimales ---------------------------------

def _solo_cadena(v: Any) -> Any:
    # Decimal pasa para cuando el backend arma la respuesta; JSON solo admite cadena.
    if isinstance(v, (str, Decimal)):
        return v
    raise ValueError('debe enviarse como cadena decimal, por ejemplo "15000.00"')


_ENTRADA = BeforeValidator(_solo_cadena)
_SALIDA = PlainSerializer(lambda v: f"{v:.2f}", return_type=str, when_used="json")
_ESQUEMA = WithJsonSchema(
    {"type": "string", "pattern": r"^-?\d+(\.\d{1,2})?$", "examples": ["15000.00"]})

# NUMERIC(14,2); admite negativos y 0.
Importe = Annotated[Decimal, _ENTRADA, Field(max_digits=14, decimal_places=2), _SALIDA, _ESQUEMA]
# NUMERIC(5,2) con CHECK (> 0 AND <= 100).
Porcentaje = Annotated[Decimal, _ENTRADA,
                       Field(max_digits=5, decimal_places=2, gt=0, le=100), _SALIDA, _ESQUEMA]
# NUMERIC(5,2) con CHECK (> 0).
UmbralPct = Annotated[Decimal, _ENTRADA,
                      Field(max_digits=5, decimal_places=2, gt=0), _SALIDA, _ESQUEMA]


# --- Período: primer día del mes ---------------------------------------------

def _primer_dia(v: date) -> date:
    if v.day != 1:
        raise ValueError("el período debe ser el primer día del mes (AAAA-MM-01)")
    return v


Periodo = Annotated[date, AfterValidator(_primer_dia),
                    WithJsonSchema({"type": "string", "format": "date",
                                    "pattern": r"^\d{4}-\d{2}-01$", "examples": ["2026-09-01"]})]