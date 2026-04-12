"""
Settings module for the AI service backend.
Reads configuration from environment variables with default values.
"""

import os
from typing import List


class Settings:
    """Application settings loaded from environment variables"""

    # Get the directory where this settings.py file is located
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
            "AI_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080"
        ).split(",")
    ]

    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # API settings
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))

    # Safety thresholds
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.6"))
    DLS_BLOCK_THRESHOLD: float = float(os.getenv("DLS_BLOCK_THRESHOLD", "3.0"))

    @classmethod
    def to_dict(cls) -> dict:
        """Return settings as dictionary"""
        return {
            "excel_path": cls.EXCEL_PATH,
            "model_path": cls.MODEL_PATH,
            "cors_origins": cls.CORS_ORIGINS,
            "log_level": cls.LOG_LEVEL,
            "confidence_threshold": cls.CONFIDENCE_THRESHOLD,
            "dls_block_threshold": cls.DLS_BLOCK_THRESHOLD,
        }


# Export default settings instance
settings = Settings()
