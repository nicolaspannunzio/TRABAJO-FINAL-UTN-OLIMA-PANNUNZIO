"""B4 / HU-10: tabla de casos de la función pura de variación. Sin base de datos."""
from decimal import Decimal as D

import pytest

from app.modules.advertencias.calculo import evaluar, umbral_efectivo, variacion_pct

GLOBAL = D("30.00")
PROPIO_50 = D("50.00")


@pytest.mark.parametrize(
    ("caso", "anterior", "actual", "umbral_concepto", "tipo", "variacion"),
    [
        # Criterio 1: sin umbral propio, $1.000 → $1.350 (35 %) advierte; → $1.200 (20 %) no.
        ("35 % con umbral global", D("1000.00"), D("1350.00"), None, "variacion_inusual", D("35")),
        ("20 % con umbral global", D("1000.00"), D("1200.00"), None, None, D("20")),
        # Criterio 2: con umbral propio 50 %, $1.350 (35 %) no advierte.
        ("35 % con umbral propio 50", D("1000.00"), D("1350.00"), PROPIO_50, None, D("35")),
        # Criterio 3: $1.000 → −$200 es una variación de 120 %.
        ("1000 a -200 (120 %)", D("1000.00"), D("-200.00"), None, "variacion_inusual", D("120")),
        # Criterio 4: sin importe anterior o anterior en 0 → solo sin_referencia.
        ("sin importe anterior", None, D("1350.00"), None, "sin_referencia", None),
        ("anterior en 0", D("0.00"), D("1350.00"), None, "sin_referencia", None),
        # Bordes.
        ("exactamente en el umbral no advierte", D("1000.00"), D("1300.00"), None, None, D("30")),
        ("apenas sobre el umbral advierte", D("1000.00"), D("1300.01"), None, "variacion_inusual",
         D("30.001")),
        ("baja de 40 % también advierte", D("1000.00"), D("600.00"), None, "variacion_inusual", D("40")),
        ("anterior negativo usa el valor absoluto", D("-1000.00"), D("-1350.00"), None,
         "variacion_inusual", D("35")),
        ("sin cambio", D("1000.00"), D("1000.00"), None, None, D("0")),
        ("actual en 0 contra 1000 es 100 %", D("1000.00"), D("0.00"), None, "variacion_inusual",
         D("100")),
    ],
)
def test_evaluar(caso, anterior, actual, umbral_concepto, tipo, variacion):
    resultado = evaluar(actual, anterior, umbral_efectivo(umbral_concepto, GLOBAL))

    assert resultado.tipo == tipo, caso
    if variacion is None:
        assert resultado.variacion_pct is None, caso
    else:
        assert resultado.variacion_pct == variacion, caso


def test_umbral_efectivo_usa_el_propio_si_existe_y_si_no_el_global():
    assert umbral_efectivo(PROPIO_50, GLOBAL) == PROPIO_50
    assert umbral_efectivo(None, GLOBAL) == GLOBAL


def test_todo_en_decimal_sin_float():
    v = variacion_pct(D("1000.00"), D("1350.00"))
    assert isinstance(v, D)
    assert isinstance(evaluar(D("1350.00"), D("1000.00"), GLOBAL).variacion_pct, D)
