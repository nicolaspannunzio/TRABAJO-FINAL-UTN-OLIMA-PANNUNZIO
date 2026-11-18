# modules/reparto/service.py
"""Cálculo del reparto de una preliquidación entre propietarios (RN-21). Función pura.

No toca la base ni expone rutas: la usa preliquidaciones (B6) al generar cada versión.
Todo en Decimal: nunca float.

Regla (RN-21):
1. Cada propietario recibe total × porcentaje / 100, redondeado a 2 decimales con
   ROUND_HALF_UP (la mitad se redondea alejándose de cero: 2,345 → 2,35; −2,345 → −2,35).
2. El último propietario, en orden ascendente de id, no se redondea: recibe lo que falta
   para llegar al total. Así la suma del reparto es SIEMPRE exactamente el total.

Ejemplo: $10,00 con 33,33 / 33,33 / 33,34 → 3,33 / 3,33 / 3,34 (suma 10,00).
"""
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

CENTAVO = Decimal("0.01")
CIEN = Decimal("100")


@dataclass(frozen=True)
class Cuota:
    propietario_id: UUID
    porcentaje: Decimal  # el porcentaje aplicado, tal como vino (se copia a reparto.porcentaje_aplicado)
    importe: Decimal  # importe_correspondiente, con 2 decimales; puede ser negativo


def repartir(total: Decimal, porcentajes: dict[UUID, Decimal]) -> list[Cuota]:
    """Reparte `total` según `porcentajes` ({propietario_id: porcentaje}).

    Devuelve una Cuota por propietario, en orden ascendente de id. La suma de los importes
    es exactamente `total` redondeado a centavos.

    Lanza ValueError si no hay propietarios o si los porcentajes no suman 100: la
    preliquidación valida eso antes y responde 409 (propiedad_sin_reparto, reparto_invalido),
    así que acá es una protección contra un uso incorrecto, no un caso esperado.
    """
    if not porcentajes:
        raise ValueError("No hay propietarios para repartir")
    suma = sum(porcentajes.values(), Decimal("0"))
    if suma != CIEN:
        raise ValueError(f"Los porcentajes suman {suma}, no 100")

    total = total.quantize(CENTAVO, rounding=ROUND_HALF_UP)
    ids = sorted(porcentajes)  # UUID se ordena igual que en PostgreSQL (byte a byte)

    cuotas: list[Cuota] = []
    asignado = Decimal("0")
    for propietario_id in ids[:-1]:
        porcentaje = porcentajes[propietario_id]
        importe = (total * porcentaje / CIEN).quantize(CENTAVO, rounding=ROUND_HALF_UP)
        cuotas.append(Cuota(propietario_id, porcentaje, importe))
        asignado += importe

    ultimo = ids[-1]
    cuotas.append(Cuota(ultimo, porcentajes[ultimo], total - asignado))
    return cuotas
