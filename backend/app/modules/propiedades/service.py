# modules/propiedades/service.py
"""HU-03: alta y edición de propiedades y propietarios (RN-05)."""

from decimal import Decimal
from uuid import UUID

from sqlmodel import Session

from app.core.errors import AppError
from app.modules.propiedades import repository
from app.modules.propiedades.models import Propiedad, Propietario
from app.modules.propiedades.schemas import (
    PropiedadActualizar,
    PropiedadCrear,
    PropietarioActualizar,
    PropietarioCrear,
    RepartoEntrada,
)


def _propiedad_no_encontrada(propiedad_id: UUID) -> AppError:
    return AppError(
        404,
        "propiedad_no_encontrada",
        "La propiedad no existe",
        {"propiedad_id": str(propiedad_id)},
    )


def _propietario_no_encontrado(propietario_id: UUID) -> AppError:
    return AppError(
        404,
        "propietario_no_encontrado",
        "El propietario no existe",
        {"propietario_id": str(propietario_id)},
    )


# --- Propiedades ---------------------------------------------------------------


def listar(session: Session) -> list[Propiedad]:
    return repository.listar(session)


def obtener(session: Session, propiedad_id: UUID) -> Propiedad:
    propiedad = repository.obtener(session, propiedad_id)
    if propiedad is None:
        raise _propiedad_no_encontrada(propiedad_id)
    return propiedad


def crear(session: Session, datos: PropiedadCrear) -> Propiedad:
    # Criterio 1 de HU-03: sin estado explícito queda `activa` (default del schema y del DDL).
    return repository.crear(session, datos.model_dump())


def actualizar(
    session: Session, propiedad_id: UUID, datos: PropiedadActualizar
) -> Propiedad:
    propiedad = obtener(session, propiedad_id)
    # exclude_unset: solo se tocan los campos que vinieron en el PATCH.
    return repository.actualizar(
        session, propiedad, datos.model_dump(exclude_unset=True)
    )


# --- Propietarios --------------------------------------------------------------


def listar_propietarios(session: Session) -> list[Propietario]:
    return repository.listar_propietarios(session)


def obtener_propietario(session: Session, propietario_id: UUID) -> Propietario:
    propietario = repository.obtener_propietario(session, propietario_id)
    if propietario is None:
        raise _propietario_no_encontrado(propietario_id)
    return propietario


def crear_propietario(session: Session, datos: PropietarioCrear) -> Propietario:
    return repository.crear_propietario(session, datos.model_dump())


def actualizar_propietario(
    session: Session, propietario_id: UUID, datos: PropietarioActualizar
) -> Propietario:
    propietario = obtener_propietario(session, propietario_id)
    return repository.actualizar_propietario(
        session, propietario, datos.model_dump(exclude_unset=True)
    )


# --- Reparto (HU-03 criterio 2, HU-04) --------------------------------------------


def validar_reparto(entradas: list[RepartoEntrada]) -> None:
    """Reglas RN-05 y RN-06. No toca la base: se prueba sin DB."""
    ids = [e.propietario_id for e in entradas]
    repetidos = sorted({str(i) for i in ids if ids.count(i) > 1})
    if repetidos:
        raise AppError(
            422,
            "propietario_repetido",
            "Un propietario no puede repetirse en la misma propiedad",
            {"propietarios": repetidos},
        )
    suma = sum((e.porcentaje for e in entradas), Decimal("0"))
    if suma != Decimal("100"):
        raise AppError(
            422,
            "reparto_suma_invalida",
            f"Los porcentajes deben sumar 100 y suman {suma:.2f}",
            {"suma": f"{suma:.2f}"},
        )


def obtener_reparto(session: Session, propiedad_id: UUID) -> list[dict]:
    obtener(session, propiedad_id)  # 404 si la propiedad no existe
    return repository.reparto_vigente(session, propiedad_id)


def reemplazar_reparto(
    session: Session, propiedad_id: UUID, entradas: list[RepartoEntrada]
) -> list[dict]:
    validar_reparto(entradas)  # antes de abrir nada en la base
    if repository.bloquear_propiedad(session, propiedad_id) is None:
        session.rollback()
        raise _propiedad_no_encontrada(propiedad_id)
    ids = [e.propietario_id for e in entradas]
    existentes = repository.propietarios_existentes(session, ids)
    faltantes = [i for i in ids if i not in existentes]
    if faltantes:
        session.rollback()
        raise _propietario_no_encontrado(faltantes[0])
    try:
        repository.reemplazar_reparto(
            session, propiedad_id, [(e.propietario_id, e.porcentaje) for e in entradas]
        )
    except Exception:
        session.rollback()  # ante cualquier fallo quedan los porcentajes anteriores
        raise
    return repository.reparto_vigente(session, propiedad_id)
