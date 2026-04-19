"""
Settings module for the AI service backend.
Reads configuration from environment variables with default values.
"""

import os
import sys
from typing import List


def _require_secret_key() -> str:
    """
    Return SECRET_KEY from environment.

    In production (APP_ENV=production) the key MUST be set explicitly;
    the application will refuse to start with a missing or placeholder value.
    In other environments a development-only default is used so the service
    starts without extra setup.
    """
    key = os.getenv("SECRET_KEY", "")
    app_env = os.getenv("APP_ENV", "development").lower()

    insecure_placeholders = {
        "",
        "your-secret-key-change-in-production",
        "your-super-secret-key-change-in-production",
        "REPLACE_WITH_STRONG_RANDOM_SECRET",
    }

    if app_env == "production":
        if not key or key in insecure_placeholders:
            print(
                "FATAL: SECRET_KEY environment variable is not set or uses an insecure "
                "placeholder value. Generate a strong key with:\n"
                "    openssl rand -hex 32\n"
                "and set it as the SECRET_KEY environment variable before starting "
                "the application in production.",
                file=sys.stderr,
            )
            sys.exit(1)

    # Development / CI fallback — never acceptable in production
    return key or "dev-only-insecure-key-do-not-use-in-production"


class Settings:
    """Application settings loaded from environment variables"""

    # Get the directory where this settings.py file is located
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # JWT secret — validated at startup via _require_secret_key()
    SECRET_KEY: str = _require_secret_key()

    # Model and data settings
    EXCEL_PATH: str = os.getenv(
        "EXCEL_PATH", os.path.join(_BASE_DIR, "models", "rss_dashboard_dataset_built_recalc.xlsx")
    )
    MODEL_PATH: str = os.getenv("MODEL_PATH", os.path.join(_BASE_DIR, "models", "recommendation_model.joblib"))
    SCHEMA_PATH: str = os.getenv("SCHEMA_PATH", os.path.join(_BASE_DIR, "models", "schema.joblib"))
    METRICS_PATH: str = os.getenv("METRICS_PATH", os.path.join(_BASE_DIR, "models", "metrics.json"))

    # CORS settings
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "AI_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080,http://localhost:8081,http://127.0.0.1:8081"
        ).split(",")
    ]

    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # API settings
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))

    # System operating mode — SIMULATION (default) or PROTOTYPE
    _raw_mode = os.getenv("SYSTEM_MODE", "SIMULATION").upper().strip()
    SYSTEM_MODE: str = _raw_mode if _raw_mode in ("SIMULATION", "PROTOTYPE") else "SIMULATION"

    # Safety thresholds
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.6"))
    DLS_BLOCK_THRESHOLD: float = float(os.getenv("DLS_BLOCK_THRESHOLD", "3.0"))

    # Actuator settings
    ACTUATOR_DERATE_THRESHOLD: float = float(os.getenv("ACTUATOR_DERATE_THRESHOLD", "0.65"))

    @classmethod
    def to_dict(cls) -> dict:
        """Return settings as dictionary"""
        return {
            "system_mode": cls.SYSTEM_MODE,
            "excel_path": cls.EXCEL_PATH,
            "model_path": cls.MODEL_PATH,
            "cors_origins": cls.CORS_ORIGINS,
            "log_level": cls.LOG_LEVEL,
            "confidence_threshold": cls.CONFIDENCE_THRESHOLD,
            "dls_block_threshold": cls.DLS_BLOCK_THRESHOLD,
            "actuator_derate_threshold": cls.ACTUATOR_DERATE_THRESHOLD,
        }


# Export default settings instance
settings = Settings()
