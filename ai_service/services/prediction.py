"""
Core decision pipeline: inference → PETE → gate → actuator → response.
No database dependency — callers handle persistence.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple, List
import logging

import pandas as pd

from schemas import (
    PredictRequest, PredictResponse, DecisionRecord,
    PeteStatus, PeteParameterStatus, Limits,
)
import model_loader
from pete_envelope import evaluate_envelope
from actuator import virtual_actuator
from settings import settings
from logging_config import log_actuator_event
from services.config_builder import build_limits, build_pete_config

logger = logging.getLogger(__name__)


# ── Pure business-logic functions ──

def calculate_recommendation(dls: float, inclination: float, vibration: float) -> str:
    """Rule-based recommendation logic."""
    if dls > 6:
        return "Hold"
    elif inclination > 45:
        return "Drop"
    else:
        return "Build"

def calculate_confidence(dls: float, vibration: float, torque: float) -> float:
    """Calculate confidence based on how far values are from limits."""
    confidence = 0.95
    if dls > 4:
        confidence -= (dls - 4) * 0.05
    if dls > 6:
        confidence -= (dls - 6) * 0.1
    if vibration > 2:
        confidence -= (vibration - 2) * 0.1
    if torque > 30000 or torque < 5000:
        confidence -= 0.1
    return max(0.55, min(0.95, confidence))

def determine_gate_status(confidence: float, dls: float, vibration: float) -> Tuple[str, Optional[str]]:
    """Determine gate status and rejection reason (hardcoded thresholds)."""
    if confidence < 0.6 or dls > 8:
        reason = "LOW_CONFIDENCE" if confidence < 0.6 else "LIMIT_EXCEEDED"
        return "REJECTED", reason
    elif dls >= 6 or vibration > 3:
        return "REDUCED", None
    else:
        return "ACCEPTED", None

def determine_gate_status_config(confidence: float, dls: float, vibration: float, limits: Limits) -> Tuple[str, Optional[str]]:
    """Determine gate status using config limits."""
    if confidence < limits.confidence_reject_threshold or dls > limits.dls_reject_threshold or vibration > limits.vibration_reject_threshold:
        if confidence < limits.confidence_reject_threshold:
            reason = "LOW_CONFIDENCE"
        elif dls > limits.dls_reject_threshold:
            reason = "DLS_LIMIT_EXCEEDED"
        else:
            reason = "VIBRATION_LIMIT_EXCEEDED"
        return "REJECTED", reason
    elif dls >= limits.dls_reduce_threshold or vibration > limits.vibration_reduce_threshold:
        return "REDUCED", None
    else:
        return "ACCEPTED", None

def get_event_tags(dls: float, vibration: float, confidence: float) -> List[str]:
    """Generate event tags based on conditions."""
    tags = []
    if dls > 6:
        tags.append("high_dls")
    if vibration > 3:
        tags.append("high_vibration")
    if confidence < 0.7:
        tags.append("low_confidence")
    return tags


# ── Pipeline result ──

@dataclass
class PipelineResult:
    """Everything callers need from the decision pipeline."""
    response: PredictResponse
    decision_record: DecisionRecord
    recommendation: str
    confidence: float
    gate_status: str
    rejection_reason: Optional[str]
    model_version: str
    event_tags: List[str]
    actuator_outcome: str


# ── Private helpers ──

def _build_model_input(request: PredictRequest) -> pd.DataFrame:
    """Construct the DataFrame the ML model expects."""
    return pd.DataFrame([{
        'Formation_Class': request.Formation_Class or 'Cleaner sand',
        'WOB_klbf': request.WOB_klbf,
        'RPM_demo': request.RPM_demo,
        'ROP_ft_hr': request.ROP_ft_hr,
        'PHIF': request.PHIF if request.PHIF is not None else 0.18,
        'VSH': request.VSH if request.VSH is not None else 0.25,
        'SW': request.SW if request.SW is not None else 0.35,
        'KLOGH': request.KLOGH if request.KLOGH is not None else 120,
        'Torque_kftlb': request.Torque_kftlb,
        'Vibration_g': request.Vibration_g,
        'DLS_deg_per_100ft': request.DLS_deg_per_100ft,
        'Inclination_deg': request.Inclination_deg,
        'Azimuth_deg': request.Azimuth_deg,
    }])


def _build_pete_status(pete_result) -> PeteStatus:
    """Convert pete_envelope result to API PeteStatus model."""
    return PeteStatus(
        overall_status=pete_result.overall_status,
        parameter_margins=[
            PeteParameterStatus(
                name=pm.name, value=pm.value, lower_limit=pm.lower_limit,
                upper_limit=pm.upper_limit, margin=pm.margin, status=pm.status,
            )
            for pm in pete_result.parameter_margins
        ],
        violations=pete_result.violations,
        max_dls_change=pete_result.max_dls_change,
        formation_sensitivity=pete_result.formation_sensitivity,
    )


def _build_alert_message(gate_status: str, rejection_reason: Optional[str]) -> str:
    """Build human-readable alert message from gate outcome."""
    if gate_status == "REJECTED":
        return f"Recommendation rejected: {rejection_reason}"
    elif gate_status == "REDUCED":
        return "Recommendation accepted with reduced aggressiveness"
    else:
        return "Recommendation accepted"


# ── Core pipeline ──

def run_decision_pipeline(request: PredictRequest, raw_config: dict) -> PipelineResult:
    """
    Shared decision pipeline: inference → PETE → gate → actuator → response.

    Does NOT persist to database or create alerts — callers handle that.
    Testable with no DB session: pass a config dict and a PredictRequest.
    """
    limits = build_limits(raw_config)

    # 1. Model inference or rule-based fallback
    if model_loader.model_available and model_loader.ml_model is not None:
        model_version = "rf-cal-v1"
        input_data = _build_model_input(request)
        recommendation = model_loader.ml_model.predict(input_data)[0]
        probabilities = model_loader.ml_model.predict_proba(input_data)[0]
        confidence = float(max(probabilities))
    else:
        model_version = "rules-v1"
        recommendation = calculate_recommendation(
            request.DLS_deg_per_100ft, request.Inclination_deg, request.Vibration_g
        )
        confidence = calculate_confidence(
            request.DLS_deg_per_100ft, request.Vibration_g, request.Torque_kftlb
        )

    # 2. PETE operating envelope evaluation
    pete_config = build_pete_config(raw_config)
    pete_result = evaluate_envelope(
        wob=request.WOB_klbf, rpm=request.RPM_demo,
        torque=request.Torque_kftlb, vibration=request.Vibration_g,
        dls=request.DLS_deg_per_100ft, inclination=request.Inclination_deg,
        config=pete_config, formation_class=request.Formation_Class,
    )

    # 3. Gate decision
    gate_status, rejection_reason = determine_gate_status_config(
        confidence, request.DLS_deg_per_100ft, request.Vibration_g, limits
    )

    # 4. PETE overrides
    if pete_result.overall_status == "OUTSIDE_LIMITS" and gate_status != "REJECTED":
        gate_status = "REJECTED"
        rejection_reason = f"PETE_ENVELOPE_VIOLATION: {', '.join(pete_result.violations)}"
    elif pete_result.overall_status == "NEAR_LIMIT" and gate_status == "ACCEPTED":
        gate_status = "REDUCED"
        rejection_reason = f"PETE_NEAR_LIMIT: {', '.join(pete_result.violations)}"

    # 5. Build response components
    pete_status = _build_pete_status(pete_result)
    alert_message = _build_alert_message(gate_status, rejection_reason)
    event_tags = get_event_tags(request.DLS_deg_per_100ft, request.Vibration_g, confidence)
    event_tags.extend([v.lower() for v in pete_result.violations])

    # 6. Decision record
    decision_record = DecisionRecord(
        timestamp=datetime.utcnow().isoformat(),
        model_version=model_version,
        feature_summary={
            "WOB_klbf": request.WOB_klbf,
            "RPM_demo": request.RPM_demo,
            "ROP_ft_hr": request.ROP_ft_hr,
            "Torque_kftlb": request.Torque_kftlb,
            "Vibration_g": request.Vibration_g,
            "DLS_deg_per_100ft": request.DLS_deg_per_100ft,
            "Inclination_deg": request.Inclination_deg,
            "Azimuth_deg": request.Azimuth_deg,
        },
        steering_command=recommendation,
        confidence_score=confidence,
        gate_outcome=gate_status,
        rejection_reason=rejection_reason,
        execution_status="BLOCKED" if gate_status == "REJECTED" else (
            "SIMULATED_SENT" if settings.SYSTEM_MODE == "SIMULATION" else "SENT"
        ),
        fallback_mode="HOLD_STEERING" if gate_status == "REJECTED" else None,
        event_tags=event_tags,
        pete_status=pete_status.model_dump() if pete_status else None,
        system_mode=settings.SYSTEM_MODE,
    )

    # 7. Actuator execution
    actuator_response = virtual_actuator.execute(
        command=recommendation, gate_outcome=gate_status,
        confidence=confidence, system_mode=settings.SYSTEM_MODE,
    )
    decision_record.actuator_outcome = actuator_response.outcome.value

    # 8. Log actuator event
    log_actuator_event(
        logger, command=recommendation,
        outcome=actuator_response.outcome.value,
        state=actuator_response.state.value,
        is_simulated=actuator_response.is_simulated,
        message=actuator_response.message,
        system_mode=settings.SYSTEM_MODE,
    )

    # 9. Build response
    response = PredictResponse(
        recommendation=recommendation, confidence=confidence,
        gate_status=gate_status, alert_message=alert_message,
        decision_record=decision_record, pete_status=pete_status,
        system_mode=settings.SYSTEM_MODE,
        actuator_status=virtual_actuator.get_status(),
    )

    return PipelineResult(
        response=response, decision_record=decision_record,
        recommendation=recommendation, confidence=confidence,
        gate_status=gate_status, rejection_reason=rejection_reason,
        model_version=model_version, event_tags=event_tags,
        actuator_outcome=actuator_response.outcome.value,
    )
