"""A1 / HU-01 criterio 4: con RLS activada y sin policies, anon y authenticated
(los roles de la Data API de Supabase) no ven ninguna fila."""
import pytest
from sqlalchemy import text


def test_no_hay_policies(db):
    n = db.connection().execute(
        text("SELECT count(*) FROM pg_policies WHERE schemaname = 'public'")).scalar()
    assert n == 0


@pytest.mark.parametrize("rol", ["anon", "authenticated"])
def test_data_api_no_devuelve_filas(db, rol):
    conn = db.connection()
    # En Supabase estos roles existen y tienen SELECT sobre public. Se reproduce dentro
    # de la transacción del test: el fixture db la descarta al cerrar.
    conn.execute(text(f"""
        DO $$ BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{rol}') THEN
            CREATE ROLE {rol} NOLOGIN;
          END IF;
        END $$"""))
    conn.execute(text(f"GRANT USAGE ON SCHEMA public TO {rol}"))
    conn.execute(text(f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {rol}"))
    conn.execute(text("INSERT INTO propiedad (direccion) VALUES ('Calle Falsa 123')"))

    # Como dueño hay filas (el dueño ignora RLS)...
    assert conn.execute(text("SELECT count(*) FROM rol")).scalar() == 2
    assert conn.execute(text("SELECT count(*) FROM propiedad")).scalar() > 0

    # ...y como anon / authenticated no se ve ninguna.
    conn.execute(text(f"SET LOCAL ROLE {rol}"))
    try:
        for tabla in ("rol", "propiedad", "usuario"):
            assert conn.execute(text(f"SELECT count(*) FROM {tabla}")).scalar() == 0
    finally:
        conn.execute(text("RESET ROLE"))