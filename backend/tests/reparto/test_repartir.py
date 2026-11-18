"""B5 / HU-11 (RN-21): reparto con redondeo. Función pura, sin base de datos."""
import random
import uuid
from decimal import Decimal as D

import pytest

from app.modules.reparto.service import Cuota, repartir

# ids fijos y ordenados: P1 < P2 < P3, así se sabe quién es "el último".
P1 = uuid.UUID("00000000-0000-4000-8000-000000000001")
P2 = uuid.UUID("00000000-0000-4000-8000-000000000002")
P3 = uuid.UUID("00000000-0000-4000-8000-000000000003")


def _importes(cuotas: list[Cuota]) -> list[D]:
    return [c.importe for c in cuotas]


# --- Tabla de casos ----------------------------------------------------------

@pytest.mark.parametrize(
    ("caso", "total", "porcentajes", "esperado"),
    [
        # Done cuando de B5: $10,00 con 33,33 / 33,33 / 33,34 → 3,33 / 3,33 / 3,34.
        ("ejemplo del plan", D("10.00"), {P1: D("33.33"), P2: D("33.33"), P3: D("33.34")},
         [D("3.33"), D("3.33"), D("3.34")]),
        # Done cuando de B5: con −$500 los importes son negativos.
        ("total negativo 50/50", D("-500.00"), {P1: D("50"), P2: D("50")},
         [D("-250.00"), D("-250.00")]),
        ("50/50 exacto", D("1000.00"), {P1: D("50"), P2: D("50")}, [D("500.00"), D("500.00")]),
        ("60/40", D("1000.00"), {P1: D("60"), P2: D("40")}, [D("600.00"), D("400.00")]),
        ("un solo propietario al 100", D("1234.56"), {P1: D("100")}, [D("1234.56")]),
        ("total cero", D("0.00"), {P1: D("50"), P2: D("50")}, [D("0.00"), D("0.00")]),
        # El último absorbe el centavo que sobra: 0,01 al 50/50.
        ("un centavo al 50/50", D("0.01"), {P1: D("50"), P2: D("50")}, [D("0.01"), D("0.00")]),
        # ROUND_HALF_UP: 0,005 sube a 0,01 (con ROUND_HALF_EVEN bajaría a 0,00).
        ("mitad hacia arriba", D("10.01"), {P1: D("50"), P2: D("50")}, [D("5.01"), D("5.00")]),
        # ROUND_HALF_UP con negativos: la mitad se aleja de cero.
        ("mitad hacia arriba negativa", D("-10.01"), {P1: D("50"), P2: D("50")},
         [D("-5.01"), D("-5.00")]),
        ("tres tercios de 100", D("100.00"), {P1: D("33.33"), P2: D("33.33"), P3: D("33.34")},
         [D("33.33"), D("33.33"), D("33.34")]),
    ],
)
def test_repartir(caso, total, porcentajes, esperado):
    cuotas = repartir(total, porcentajes)

    assert _importes(cuotas) == esperado, caso
    assert sum(_importes(cuotas), D("0")) == total, caso


def test_el_orden_es_por_id_ascendente_aunque_lleguen_desordenados():
    cuotas = repartir(D("10.00"), {P3: D("33.34"), P1: D("33.33"), P2: D("33.33")})

    assert [c.propietario_id for c in cuotas] == [P1, P2, P3]
    assert _importes(cuotas) == [D("3.33"), D("3.33"), D("3.34")]


def test_el_ultimo_por_id_absorbe_la_diferencia():
    # El porcentaje mayor (33,34) lo tiene P2, pero quien absorbe la diferencia es
    # P3, el de mayor id: la regla mira el id, no el porcentaje.
    cuotas = repartir(D("10.00"), {P1: D("33.33"), P2: D("33.34"), P3: D("33.33")})

    # P1: 3,333 → 3,33; P2: 3,334 → 3,33; P3: 10 − 6,66 = 3,34.
    assert _importes(cuotas) == [D("3.33"), D("3.33"), D("3.34")]


def test_cada_cuota_guarda_su_porcentaje_aplicado():
    cuotas = repartir(D("1000.00"), {P1: D("60.00"), P2: D("40.00")})

    assert [c.porcentaje for c in cuotas] == [D("60.00"), D("40.00")]


def test_todo_en_decimal_con_dos_decimales():
    for c in repartir(D("10.00"), {P1: D("33.33"), P2: D("33.33"), P3: D("33.34")}):
        assert isinstance(c.importe, D)
        assert c.importe.as_tuple().exponent == -2


# --- Errores de uso ----------------------------------------------------------

def test_sin_propietarios_es_un_error():
    with pytest.raises(ValueError):
        repartir(D("100.00"), {})


@pytest.mark.parametrize("porcentajes", [
    {P1: D("50"), P2: D("40")},   # suma 90
    {P1: D("60"), P2: D("50")},   # suma 110
])
def test_porcentajes_que_no_suman_100_son_un_error(porcentajes):
    with pytest.raises(ValueError):
        repartir(D("100.00"), porcentajes)


# --- Propiedad de invariancia ------------------------------------------------

def _porcentajes_al_azar(rng: random.Random, n: int) -> dict[uuid.UUID, D]:
    """n porcentajes con 2 decimales, todos > 0, que suman exactamente 100."""
    cortes = sorted(rng.sample(range(1, 10000), n - 1))
    partes = [b - a for a, b in zip([0, *cortes], [*cortes, 10000])]  # en centésimos
    return {uuid.UUID(int=rng.getrandbits(128)): D(p) / 100 for p in partes}


def test_la_suma_siempre_es_el_total():
    """2.000 repartos al azar: la suma da siempre exactamente el total, y cada cuota salvo
    la última está a menos de medio centavo del valor exacto."""
    rng = random.Random(20261121)  # semilla fija: el test siempre prueba los mismos casos
    for _ in range(2000):
        n = rng.randint(1, 6)
        porcentajes = _porcentajes_al_azar(rng, n)
        total = D(rng.randint(-10_000_000, 10_000_000)) / 100

        cuotas = repartir(total, porcentajes)

        assert sum(_importes(cuotas), D("0")) == total
        for c in cuotas[:-1]:
            exacto = total * c.porcentaje / 100
            assert abs(c.importe - exacto) <= D("0.005")
