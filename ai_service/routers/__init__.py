"""Router registry — import and assemble all API routers."""

from .health import router as health_router
from .auth_routes import router as auth_router
from .predict import router as predict_router
from .telemetry import router as telemetry_router
from .actuator_routes import router as actuator_router
from .config import router as config_router
from .decisions import router as decisions_router
from .admin import router as admin_router
from .metrics import router as metrics_router

all_routers = [
    health_router,
    auth_router,
    predict_router,
    telemetry_router,
    actuator_router,
    config_router,
    decisions_router,
    admin_router,
    metrics_router,
]
