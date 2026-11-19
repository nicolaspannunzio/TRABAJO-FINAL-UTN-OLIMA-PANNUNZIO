# modules/preliquidaciones/service.py
"""HU-11: generar la preliquidación (RN-17 a RN-22, RN-24).
HU-12: consultar versiones, la vigente y el detalle de cada una (RN-21, RN-22).

Pasos, en una sola transacción:
 1. Validaciones que no escriben nada: propiedad (404), checklist (409), pendientes sin
    confirmar (409), reparto (409).
 2. Detalle: solo los conceptos `cargado` (incluido $0). Total = suma del detalle (RN-19).
 3. Advertencias: las de variación (las mismas de la vista previa, HU-10), una
    `pendiente_confirmado` por pendiente (RN-18) y `total_negativo` si corresponde (RN-20).
 4. Reparto con `repartir` (B5): copia el porcentaje vigente y calcula cada importe (RN-21).
 5. Versión = máxima + 1 (RN-22); si otra generación simultánea tomó la misma, 409.
 6. Auditoría y commit (RN-24).
Las advertencias nunca bloquean (RN-17).

preliquidaciones, advertencias y reparto son de B: se usan directamente.
"""
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlmodel import Session

from app import audit
from app.core.errors import AppError
from app.modules.advertencias import service as advertencias_service
from app.modules.preliquidaciones import repository
from app.modules.preliquidaciones.schemas import (PreliquidacionCrear, PreliquidacionOut,
                                                  PreliquidacionResumen)
from app.modules.reparto.service import repartir

CIEN = Decimal("100")


def _detalle_error(propiedad_id: UUID, periodo: date) -> dict:
    return {"propiedad_id": str(propiedad_id), "periodo": periodo.isoformat()}


def generar(session: Session, usuario_id: UUID, datos: PreliquidacionCrear) -> PreliquidacionOut:
    propiedad_id, periodo = datos.propiedad_id, datos.periodo

    # 1. Validaciones (no escriben nada) ----------------------------------------
    if not repository.propiedad_existe(session, propiedad_id):
        raise AppError(404, "propiedad_no_encontrada", "La propiedad no existe",
                       {"propiedad_id": str(propiedad_id)})

    filas = repository.filas_checklist(session, propiedad_id, periodo)
    if not filas:
        raise AppError(409, "periodo_sin_checklist",
                       "El período no está abierto: abrí el checklist antes de generar",
                       _detalle_error(propiedad_id, periodo))

    pendientes = [f for f in filas if f["estado"] == "pendiente"]
    if pendientes and not datos.confirmar_pendientes:
        # RN-18: se bloquea e informa cuáles faltan. El usuario puede reintentar confirmando.
        raise AppError(409, "pendientes_sin_confirmar",
                       "Hay conceptos pendientes de carga: confirmá para generar igual", {
                           **_detalle_error(propiedad_id, periodo),
                           "pendientes": [{"concepto_propiedad_id": str(f["concepto_propiedad_id"]),
                                           "concepto": f["concepto"]} for f in pendientes],
                       })

    porcentajes = repository.reparto_vigente(session, propiedad_id)
    if not porcentajes:
        raise AppError(409, "propiedad_sin_reparto",
                       "La propiedad no tiene propietarios con porcentaje de reparto",
                       {"propiedad_id": str(propiedad_id)})
    suma = sum(porcentajes.values(), Decimal("0"))
    if suma != CIEN:
        raise AppError(409, "reparto_invalido",
                       "Los porcentajes de reparto de la propiedad no suman 100",
                       {"propiedad_id": str(propiedad_id), "suma": f"{suma:.2f}"})

    # 2. Detalle y total (RN-19) ------------------------------------------------
    cargados = [f for f in filas if f["estado"] == "cargado"]
    detalle = [(f["concepto_id"], f["importe"]) for f in cargados]
    total = sum((i for _, i in detalle), Decimal("0.00"))

    # 3. Advertencias (RN-15 a RN-18, RN-20) ------------------------------------
    advertencias = [(a.tipo, a.detalle)
                    for a in advertencias_service.vista_previa(session, propiedad_id, periodo)]
    advertencias += [("pendiente_confirmado",
                      f"{f['concepto']}: pendiente de carga, generado con confirmación")
                     for f in pendientes]
    if total < 0:
        advertencias.append(("total_negativo", f"El importe total es negativo: {total:.2f}"))

    # 4. Reparto (RN-21) --------------------------------------------------------
    cuotas = [(c.propietario_id, c.porcentaje, c.importe) for c in repartir(total, porcentajes)]

    # 5. Versión y snapshot (RN-22) ---------------------------------------------
    version = repository.siguiente_version(session, propiedad_id, periodo)
    try:
        preliquidacion_id = repository.insertar_cabecera(session, propiedad_id, periodo, version,
                                                         total, usuario_id)
    except repository.VersionEnConflicto:
        session.rollback()  # no queda nada a medias
        raise AppError(409, "version_en_conflicto",
                       "Otra generación de este período se hizo al mismo tiempo; "
                       "volvé a intentar", {**_detalle_error(propiedad_id, periodo),
                                             "version": version})
    repository.insertar_detalle(session, preliquidacion_id, detalle)
    repository.insertar_advertencias(session, preliquidacion_id, advertencias)
    repository.insertar_reparto(session, preliquidacion_id, cuotas)

    # 6. Auditoría (RN-24) y commit ---------------------------------------------
    audit.registrar(session, usuario_id, "generar_preliquidacion", "preliquidacion",
                    preliquidacion_id, {
                        "propiedad_id": propiedad_id,
                        "periodo": periodo,
                        "version": version,
                        "importe_total": total,
                        "conceptos": len(detalle),
                        "pendientes_confirmados": len(pendientes),
                        "advertencias": len(advertencias),
                    })
    session.commit()

    return obtener(session, preliquidacion_id)


def obtener(session: Session, preliquidacion_id: UUID) -> PreliquidacionOut:
    """Una versión completa, leída solo del snapshot."""
    datos = repository.obtener(session, preliquidacion_id)
    if datos is None:
        raise AppError(404, "preliquidacion_no_encontrada", "La preliquidación no existe",
                       {"preliquidacion_id": str(preliquidacion_id)})
    return PreliquidacionOut.model_validate(datos)


def listar_versiones(session: Session, propiedad_id: UUID,
                     periodo: date) -> list[PreliquidacionResumen]:
    """Todas las versiones del período, ordenadas. Lista vacía si todavía no se generó ninguna."""
    if not repository.propiedad_existe(session, propiedad_id):
        raise AppError(404, "propiedad_no_encontrada", "La propiedad no existe",
                       {"propiedad_id": str(propiedad_id)})
    return [PreliquidacionResumen.model_validate(dict(c))
            for c in repository.listar(session, propiedad_id, periodo)]


def obtener_vigente(session: Session, propiedad_id: UUID, periodo: date) -> PreliquidacionOut:
    """La versión de mayor número (RN-22), completa."""
    preliquidacion_id = repository.id_vigente(session, propiedad_id, periodo)
    if preliquidacion_id is None:
        raise AppError(404, "preliquidacion_no_encontrada",
                       "No hay preliquidaciones generadas para ese período",
                       _detalle_error(propiedad_id, periodo))
    return obtener(session, preliquidacion_id)
