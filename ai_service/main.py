"""App factory — assembles middleware, loads model, registers routers."""

import sys
import os

# Add the current directory to Python path for consistent imports
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

from settings import settings
from model_loader import load_ml_model
from actuator import virtual_actuator
from logging_config import setup_logging
from routers import all_routers


class CORSMiddlewareFixed(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response


# Setup structured logging
logger = setup_logging(__name__, settings.LOG_LEVEL)

# Configure actuator derate threshold from settings
virtual_actuator._derate_threshold = settings.ACTUATOR_DERATE_THRESHOLD

# Load ML model on startup
load_ml_model()


def create_app() -> FastAPI:
    application = FastAPI(
        title="Drilling Insight AI Service",
        description="AI-powered steering recommendations for drill operations",
        version="1.0.0",
    )

    # Add CORS middleware FIRST, before routes
    application.add_middleware(CORSMiddlewareFixed)

    for router in all_routers:
        application.include_router(router)

    return application


app = create_app()


# Add middleware to the app instance directly as well
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
