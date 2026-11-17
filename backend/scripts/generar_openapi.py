"""Genera docs/openapi.json desde la app (F0-08).

Uso, desde backend/:
    python -m scripts.generar_openapi

No se conecta a la base: el engine se crea recién en la primera consulta.
El archivo se escribe con LF y una sola forma de serializar, para que el diff
de git (y el chequeo de F0-11) dependan solo del contrato.
"""
import json
import os
from pathlib import Path

RUTA = Path(__file__).resolve().parents[2] / "docs" / "openapi.json"


def contenido() -> str:
    # Settings exige DATABASE_URL; para generar el contrato basta un valor sin uso.
    os.environ.setdefault("DATABASE_URL", "postgresql://sin-uso/generar_openapi")
    from app.main import app

    return json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    RUTA.write_text(contenido(), encoding="utf-8", newline="\n")
    print(f"Escrito {RUTA}")


if __name__ == "__main__":
    main()