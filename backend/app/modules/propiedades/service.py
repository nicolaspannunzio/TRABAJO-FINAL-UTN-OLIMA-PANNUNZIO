# modules/propiedades/service.py
from sqlmodel import Session

from app.modules.propiedades import repository


def listar(session: Session):
    return repository.listar(session)