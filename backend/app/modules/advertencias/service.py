# modules/advertencias/service.py
"""HU-10: vista previa de advertencias (RN-15, RN-16, RN-17). No persiste ni bloquea."""
from datetime import date
from uuid import UUID

from sqlmodel import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.modules.advertencias import repository
from app.modules.advertencias.calculo import evaluar, umbral_efectivo
from app.modules.advertencias.schemas import AdvertenciaPrevia


def periodo_anterior(periodo: date) -> date:
    """El período inmediato anterior: 2026-01-01 → 2025-12-01."""
    if periodo.month == 1:
        return date(periodo.year - 1, 12, 1)
    return date(periodo.year, periodo.month - 1, 1)


def _mes(periodo: date) -> str:
    return periodo.strftime("%Y-%m")


def vista_previa(session: Session, propiedad_id: UUID, periodo: date) -> list[AdvertenciaPrevia]:
    if not repository.checklist_existe(session, propiedad_id, periodo):
        raise AppError(404, "checklist_no_encontrado",
                       "El período no está abierto para esa propiedad",
                       {"propiedad_id": str(propiedad_id), "periodo": periodo.isoformat()})

    anterior = periodo_anterior(periodo)
    umbral_global = get_settings().umbral_variacion_default_pct
    advertencias: list[AdvertenciaPrevia] = []

    for fila in repository.conceptos_cargados(session, propiedad_id, periodo, anterior):
        umbral = umbral_efectivo(fila["umbral_variacion_pct"], umbral_global)
        resultado = evaluar(fila["actual"], fila["anterior"], umbral)

        if resultado.tipo == "variacion_inusual":
            detalle = (f"{fila['concepto']}: varió {resultado.variacion_pct:.2f} % respecto de "
                       f"{_mes(anterior)} ({fila['anterior']:.2f} → {fila['actual']:.2f}); "
                       f"umbral {umbral:.2f} %")
        elif resultado.tipo == "sin_referencia":
            # RN-16: sin importe anterior, o con importe en 0, no hay contra qué comparar.
            # El texto no afirma un importe (issue #42): el mes anterior puede no haberse
            # cargado, no corresponder o tener $0, y en los tres casos no hay referencia.
            detalle = (f"{fila['concepto']}: sin importe de referencia en {_mes(anterior)}, "
                       f"no se calcula la variación")
        else:
            continue

        advertencias.append(AdvertenciaPrevia(
            concepto_propiedad_id=fila["concepto_propiedad_id"],
            tipo=resultado.tipo,
            detalle=detalle,
        ))
    return advertencias
