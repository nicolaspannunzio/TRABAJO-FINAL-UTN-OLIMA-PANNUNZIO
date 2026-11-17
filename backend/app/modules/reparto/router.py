# modules/reparto/router.py
from fastapi import APIRouter

# `reparto` no expone rutas (plan_implementacion.md, sección 4): contiene solo la función
# pura `repartir` (B5), que usa preliquidaciones. El router queda vacío para que main.py
# lo siga registrando sin publicar rutas fuera del contrato. El reparto vigente de una
# propiedad se gestiona en /propiedades/{id}/propietarios (módulo propiedades).
router = APIRouter()