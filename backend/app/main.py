from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core import db
from app.core.config import get_settings
from app.core.contract import errores
from app.core.deps import get_current_user
from app.core.errors import register_error_handlers
from app.core.me import router as me
from app.modules.advertencias.router import router as advertencias
from app.modules.checklist.router import router as checklist
from app.modules.conceptos.router import router as conceptos
from app.modules.importes.router import router as importes
from app.modules.plantilla.router import router as plantilla
from app.modules.preliquidaciones.router import router as preliquidaciones
from app.modules.propiedades.router import router as propiedades
from app.modules.reparto.router import router as reparto
from app.modules.usuarios.router import router as usuarios


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    db.dispose_engine()  # el engine se crea la primera vez que se usa


app = FastAPI(title="Preliquidación de alquileres", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().cors_allowed_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)
register_error_handlers(app)

# 401 y 403 aplican a toda ruta protegida. El 422 se declara acá para que el contrato
# muestre {codigo, mensaje, detalle} y no el HTTPValidationError por defecto de FastAPI.
for r in (usuarios, propiedades, conceptos, plantilla, reparto,
          checklist, importes, advertencias, preliquidaciones, me):
    app.include_router(r, dependencies=[Depends(get_current_user)],
                       responses=errores(401, 403, 422))


@app.get("/health", tags=["health"])
def health():
    if db.check_db():
        return {"estado": "ok", "base": "ok"}
    return JSONResponse(status_code=503, content={"estado": "degradado", "base": "error"})