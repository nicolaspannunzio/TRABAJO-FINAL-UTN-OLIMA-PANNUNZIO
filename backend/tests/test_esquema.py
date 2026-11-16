"""F0-06: la base de pruebas sale de esquema_completo.sql, con sus triggers."""
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError


def test_esquema_cargado_desde_sql(db):
    filas = db.connection().execute(text(
        "SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public'"
    )).all()
    assert len(filas) == 14
    assert all(rls for _, rls in filas)

    roles = db.connection().execute(text("SELECT nombre FROM rol ORDER BY nombre")).scalars().all()
    assert roles == ["admin", "operador"]


@pytest.mark.parametrize("sentencia", [
    "UPDATE preliquidacion SET importe_total = 0 WHERE id = :id",
    "DELETE FROM preliquidacion WHERE id = :id",
])
def test_trigger_rechaza_modificar_preliquidacion(db, crear_usuario, sentencia):
    uid = crear_usuario()
    conn = db.connection()
    propiedad_id = conn.execute(
        text("INSERT INTO propiedad (direccion) VALUES ('Calle Falsa 123') RETURNING id")
    ).scalar()
    pre_id = conn.execute(
        text("""INSERT INTO preliquidacion (propiedad_id, periodo, importe_total, generado_por)
                VALUES (:p, '2026-09-01', :total, :u) RETURNING id"""),
        {"p": propiedad_id, "total": Decimal("1000.00"), "u": uid},
    ).scalar()
    assert isinstance(pre_id, uuid.UUID)

    with pytest.raises(DBAPIError, match="inmutable"):
        conn.execute(text(sentencia), {"id": pre_id})
    # Sin commit: el fixture db descarta todo al cerrar.