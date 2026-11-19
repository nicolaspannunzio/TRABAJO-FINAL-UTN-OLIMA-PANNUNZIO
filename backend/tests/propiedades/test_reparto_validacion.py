"""A4: reglas del reparto, sin base de datos (RN-05, RN-06)."""
import uuid
from decimal import Decimal

import pytest

from app.core.errors import AppError
from app.modules.propiedades.schemas import RepartoEntrada
from app.modules.propiedades.service import validar_reparto


def _e(porcentaje: str, propietario_id=None) -> RepartoEntrada:
    return RepartoEntrada(propietario_id=propietario_id or uuid.uuid4(),
                          porcentaje=Decimal(porcentaje))


def test_suma_100_es_valida():
    validar_reparto([_e("60.00"), _e("40.00")])
    validar_reparto([_e("33.33"), _e("33.33"), _e("33.34")])
    validar_reparto([_e("100")])


@pytest.mark.parametrize("porcentajes", [["50", "40"], ["60", "50"], ["33.33", "33.33", "33.33"], []])
def test_suma_distinta_de_100_se_rechaza(porcentajes):
    with pytest.raises(AppError) as e:
        validar_reparto([_e(p) for p in porcentajes])
    assert e.value.status == 422 and e.value.codigo == "reparto_suma_invalida"


def test_propietario_repetido_se_rechaza():
    mismo = uuid.uuid4()
    with pytest.raises(AppError) as e:
        validar_reparto([_e("50", mismo), _e("50", mismo)])
    assert e.value.status == 422 and e.value.codigo == "propietario_repetido"