# modules/propiedades/service.py
"""HU-03: alta y edición de propiedades y propietarios (RN-05).

La asociación propietario-propiedad y los porcentajes (HU-04) los agrega A4.
"""
from uuid import UUID

from sqlmodel import Session

from app.core.errors import AppError
from app.modules.propiedades import repository
from app.modules.propiedades.models import Propiedad, Propietario
from app.modules.propiedades.schemas import (PropiedadActualizar, PropiedadCrear,
                                             PropietarioActualizar, PropietarioCrear)


def _propiedad_no_encontrada(propiedad_id: UUID) -> AppError:
    return AppError(404, "propiedad_no_encontrada", "La propiedad no existe",
                    {"propiedad_id": str(propiedad_id)})


def _propietario_no_encontrado(propietario_id: UUID) -> AppError:
    return AppError(404, "propietario_no_encontrado", "El propietario no existe",
                    {"propietario_id": str(propietario_id)})


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


def actualizar(session: Session, propiedad_id: UUID, datos: PropiedadActualizar) -> Propiedad:
    propiedad = obtener(session, propiedad_id)
    # exclude_unset: solo se tocan los campos que vinieron en el PATCH.
    return repository.actualizar(session, propiedad, datos.model_dump(exclude_unset=True))


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


def actualizar_propietario(session: Session, propietario_id: UUID,
                           datos: PropietarioActualizar) -> Propietario:
    propietario = obtener_propietario(session, propietario_id)
    return repository.actualizar_propietario(session, propietario,
                                             datos.model_dump(exclude_unset=True))
