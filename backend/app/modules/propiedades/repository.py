from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete
from sqlmodel import Session, select

from app.modules.propiedades.models import Propiedad, PropiedadPropietario, Propietario

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


# --- Reparto (HU-04) -----------------------------------------------------------

def bloquear_propiedad(session: Session, propiedad_id: UUID) -> Propiedad | None:
    """Trae la propiedad con FOR UPDATE: serializa dos reemplazos de la misma propiedad."""
    return session.exec(
        select(Propiedad).where(Propiedad.id == propiedad_id).with_for_update()
    ).first()


def propietarios_existentes(session: Session, ids: list[UUID]) -> set[UUID]:
    return set(session.exec(select(Propietario.id).where(Propietario.id.in_(ids))).all())


def reparto_vigente(session: Session, propiedad_id: UUID) -> list[dict]:
    filas = session.exec(
        select(PropiedadPropietario.propietario_id, Propietario.nombre,
               PropiedadPropietario.porcentaje)
        .join(Propietario, Propietario.id == PropiedadPropietario.propietario_id)
        .where(PropiedadPropietario.propiedad_id == propiedad_id)
        .order_by(Propietario.nombre, PropiedadPropietario.propietario_id)
    ).all()
    return [{"propietario_id": i, "nombre": n, "porcentaje": p} for i, n, p in filas]


def _agregar_fila(session: Session, propiedad_id: UUID, propietario_id: UUID,
                  porcentaje: Decimal) -> None:
    session.add(PropiedadPropietario(propiedad_id=propiedad_id,
                                     propietario_id=propietario_id, porcentaje=porcentaje))


def reemplazar_reparto(session: Session, propiedad_id: UUID,
                       filas: list[tuple[UUID, Decimal]]) -> None:
    """Borra el reparto y inserta el nuevo en UNA transacción: un solo COMMIT al final."""
    session.execute(delete(PropiedadPropietario)
                    .where(PropiedadPropietario.propiedad_id == propiedad_id))
    for propietario_id, porcentaje in filas:
        _agregar_fila(session, propiedad_id, propietario_id, porcentaje)
    session.commit()