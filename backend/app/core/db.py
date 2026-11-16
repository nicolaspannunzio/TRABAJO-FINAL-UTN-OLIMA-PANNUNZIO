from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from app.core.config import get_settings

pool: ConnectionPool | None = None


def init_pool() -> None:
    global pool
    s = get_settings()
    pool = ConnectionPool(
        s.database_url,
        min_size=s.db_pool_min,
        max_size=s.db_pool_max,
        kwargs={"row_factory": dict_row, "prepare_threshold": None},
        check=ConnectionPool.check_connection,
        timeout=10,
        open=False,
    )
    pool.open(wait=False)  # no tira la app si la base está caída; /health lo informa


def close_pool() -> None:
    if pool is not None:
        pool.close()


def get_conn():
    """Dependencia FastAPI: una conexión por request, con commit/rollback automático."""
    with pool.connection() as conn:
        yield conn


def check_db() -> bool:
    try:
        with pool.connection(timeout=3) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False