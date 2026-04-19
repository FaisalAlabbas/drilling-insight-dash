"""Model metrics routes."""

import logging

from fastapi import APIRouter, Depends

from database.db import get_db
import model_loader

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Metrics"])


@router.get("/model/metrics")
async def get_model_metrics(db=Depends(get_db)):
    """Get ML model metrics from loaded model."""
    try:
        if model_loader.model_available and model_loader.model_metrics:
            return {**model_loader.model_metrics, "available": True}
        else:
            return {
                "available": model_loader.model_available,
                "message": "Model not trained yet. Run 'python train.py' to train the model."
            }
    except Exception as e:
        logger.error(f"Model metrics retrieval error: {e}")
        return {
            "available": False,
            "message": f"Error retrieving model metrics: {str(e)}"
        }
