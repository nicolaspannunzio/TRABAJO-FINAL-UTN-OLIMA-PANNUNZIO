# modules/propiedades/repository.py
from sqlmodel import Session, select

from app.modules.propiedades.models import Propiedad


def listar(session: Session) -> list[Propiedad]:
    return list(session.exec(select(Propiedad).order_by(Propiedad.direccion)).all())