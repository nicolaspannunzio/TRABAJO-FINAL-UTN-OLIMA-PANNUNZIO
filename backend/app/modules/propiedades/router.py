# modules/propiedades/router.py
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.contract import errores
from app.core.db import get_session
from app.core.errors import no_implementado
from app.modules.propiedades import service
from app.modules.propiedades.schemas import (PropiedadActualizar, PropiedadCrear, PropiedadOut,
                                             PropietarioActualizar, PropietarioCrear,
                                             PropietarioOut, RepartoEntrada, RepartoVigente)

_propiedades = APIRouter(prefix="/propiedades", tags=["propiedades"])
_propietarios = APIRouter(prefix="/propietarios", tags=["propietarios"])


# --- Propiedades ---------------------------------------------------------------

@_propiedades.get("", response_model=list[PropiedadOut])
def listar_propiedades(session: Session = Depends(get_session)):
    return service.listar(session)


@_propiedades.post("", response_model=PropiedadOut, status_code=status.HTTP_201_CREATED)
def crear_propiedad(datos: PropiedadCrear, session: Session = Depends(get_session)):
    return service.crear(session, datos)


@_propiedades.get("/{propiedad_id}", response_model=PropiedadOut, responses=errores(404))
def obtener_propiedad(propiedad_id: UUID, session: Session = Depends(get_session)):
    return service.obtener(session, propiedad_id)


@_propiedades.patch("/{propiedad_id}", response_model=PropiedadOut, responses=errores(404))
def actualizar_propiedad(propiedad_id: UUID, datos: PropiedadActualizar,
                         session: Session = Depends(get_session)):
    return service.actualizar(session, propiedad_id, datos)


@_propiedades.get("/{propiedad_id}/propietarios", response_model=list[RepartoVigente],
                  responses=errores(404))
def obtener_reparto(propiedad_id: UUID):
    raise no_implementado()


@_propiedades.put("/{propiedad_id}/propietarios", response_model=list[RepartoVigente],
                  responses=errores(404))
def reemplazar_reparto(propiedad_id: UUID, datos: list[RepartoEntrada]):
    # Reemplaza todo en una transacción; la suma = 100 se valida antes del COMMIT.
    raise no_implementado()


# --- Propietarios --------------------------------------------------------------

@_propietarios.get("", response_model=list[PropietarioOut])
def listar_propietarios(session: Session = Depends(get_session)):
    return service.listar_propietarios(session)


@_propietarios.post("", response_model=PropietarioOut, status_code=status.HTTP_201_CREATED)
def crear_propietario(datos: PropietarioCrear, session: Session = Depends(get_session)):
    return service.crear_propietario(session, datos)


@_propietarios.get("/{propietario_id}", response_model=PropietarioOut, responses=errores(404))
def obtener_propietario(propietario_id: UUID, session: Session = Depends(get_session)):
    return service.obtener_propietario(session, propietario_id)


@_propietarios.patch("/{propietario_id}", response_model=PropietarioOut, responses=errores(404))
def actualizar_propietario(propietario_id: UUID, datos: PropietarioActualizar,
                           session: Session = Depends(get_session)):
    return service.actualizar_propietario(session, propietario_id, datos)


# main.py importa un solo `router` por módulo.
router = APIRouter()
router.include_router(_propiedades)
router.include_router(_propietarios)