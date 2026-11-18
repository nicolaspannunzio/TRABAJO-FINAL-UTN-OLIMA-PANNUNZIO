# modules/advertencias/calculo.py
"""Cálculo puro de la advertencia de variación (RN-15, RN-16). No toca la base.

Lo usan GET /advertencias (vista previa, HU-10) y, más adelante, la generación de la
preliquidación (HU-11), que guarda las mismas advertencias.

Todo en Decimal: nunca float.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

TipoVariacion = Literal["variacion_inusual", "sin_referencia"]


@dataclass(frozen=True)
class Evaluacion:
    """Resultado para un concepto cargado.

    tipo: None si la variación no supera el umbral (no hay advertencia).
    variacion_pct: None cuando no hay referencia (no se puede calcular).
    """
    tipo: TipoVariacion | None
    variacion_pct: Decimal | None


def umbral_efectivo(umbral_concepto: Decimal | None, umbral_global: Decimal) -> Decimal:
    """COALESCE(concepto.umbral_variacion_pct, umbral global) (RN-15)."""
    return umbral_concepto if umbral_concepto is not None else umbral_global


def variacion_pct(actual: Decimal, anterior: Decimal) -> Decimal:
    """|actual − anterior| / |anterior| × 100 (RN-15). anterior no puede ser 0."""
    return abs(actual - anterior) / abs(anterior) * 100


def evaluar(actual: Decimal, anterior: Decimal | None, umbral_pct: Decimal) -> Evaluacion:
    """Compara el importe del período con el del período inmediato anterior.

    - Sin importe anterior, o anterior en 0: no se calcula variación, solo sin_referencia (RN-16).
    - Si la variación SUPERA el umbral (estrictamente mayor): variacion_inusual (RN-15).
    - Si no lo supera: sin advertencia. Exactamente en el umbral no advierte.
    """
    if anterior is None or anterior == 0:
        return Evaluacion("sin_referencia", None)
    v = variacion_pct(actual, anterior)
    return Evaluacion("variacion_inusual" if v > umbral_pct else None, v)
