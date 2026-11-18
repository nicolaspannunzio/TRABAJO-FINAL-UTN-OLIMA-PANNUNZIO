# modules/propiedades/repository.py
from uuid import UUID

from sqlmodel import Session, select

from app.modules.propiedades.models import Propiedad, Propietario


# --- Propiedades ---------------------------------------------------------------

def listar(session: Session) -> list[Propiedad]:
    return list(session.exec(select(Propiedad).order_by(Propiedad.direccion)).all())


def obtener(session: Session, propiedad_id: UUID) -> Propiedad | None:
    return session.get(Propiedad, propiedad_id)


def crear(session: Session, datos: dict) -> Propiedad:
    propiedad = Propiedad(**datos)
    session.add(propiedad)
    session.commit()
    session.refresh(propiedad)  # trae id, estado y fecha_alta que puso la base
    return propiedad


def actualizar(session: Session, propiedad: Propiedad, cambios: dict) -> Propiedad:
    for campo, valor in cambios.items():
        setattr(propiedad, campo, valor)
    session.add(propiedad)
    session.commit()
    session.refresh(propiedad)
    return propiedad


# --- Propietarios --------------------------------------------------------------

def listar_propietarios(session: Session) -> list[Propietario]:
    return list(session.exec(select(Propietario).order_by(Propietario.nombre)).all())


def obtener_propietario(session: Session, propietario_id: UUID) -> Propietario | None:
    return session.get(Propietario, propietario_id)


def crear_propietario(session: Session, datos: dict) -> Propietario:
    propietario = Propietario(**datos)
    session.add(propietario)
    session.commit()
    session.refresh(propietario)
    return propietario


def actualizar_propietario(session: Session, propietario: Propietario, cambios: dict) -> Propietario:
    for campo, valor in cambios.items():
        setattr(propietario, campo, valor)
    session.add(propietario)
    session.commit()
    session.refresh(propietario)
    return propietario
