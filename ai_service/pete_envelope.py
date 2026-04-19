"""
PETE (Petroleum Engineering Technical Envelope) Operating Envelope Module.

Evaluates drilling parameters against configurable operating limits.
Pure-function module — no FastAPI or database dependencies.
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel


# ─── Configuration ────────────────────────────────────────────────────────────

class PeteConfig(BaseModel):
    """Configurable thresholds for the operating envelope."""

    wob_min: float = 20.0
    wob_max: float = 60.0
    rpm_min: float = 50.0
    rpm_max: float = 300.0
    torque_min: float = 0.0
    torque_max: float = 50.0
    vibration_warn: float = 0.35
    vibration_critical: float = 0.5
    dls_warn: float = 2.5
    dls_critical: float = 3.0
    inclination_max: float = 90.0
    near_limit_margin: float = 0.15  # fraction of range that counts as "near"
    formation_multipliers: Dict[str, float] = {
        "soft": 0.8,
        "medium": 1.0,
        "hard": 1.2,
    }


# ─── Result Models ────────────────────────────────────────────────────────────

ParameterStatus = Literal["OK", "NEAR_LIMIT", "OUTSIDE"]
OverallStatus = Literal["WITHIN_LIMITS", "NEAR_LIMIT", "OUTSIDE_LIMITS"]


class ParameterMargin(BaseModel):
    """Per-parameter envelope evaluation."""

    name: str
    value: float
    lower_limit: Optional[float] = None
    upper_limit: Optional[float] = None
    margin: float  # 0.0 = at boundary, 1.0 = centre of safe zone, negative = outside
    status: ParameterStatus


class PeteEnvelopeResult(BaseModel):
    """Full envelope evaluation result."""

    overall_status: OverallStatus
    parameter_margins: List[ParameterMargin]
    violations: List[str]
    max_dls_change: float
    formation_sensitivity: Optional[str] = None


# ─── Formation Mapping ────────────────────────────────────────────────────────

_FORMATION_MAP: Dict[str, str] = {
    "shale-prone": "soft",
    "shale": "soft",
    "soft": "soft",
    "transition": "medium",
    "medium": "medium",
    "sandstone": "hard",
    "cleaner sand": "hard",
    "hard": "hard",
}


def _classify_formation(formation_class: Optional[str]) -> str:
    """Map a formation class string to soft / medium / hard."""
    if not formation_class:
        return "medium"
    return _FORMATION_MAP.get(formation_class.lower().strip(), "medium")


# ─── Evaluation Helpers ───────────────────────────────────────────────────────

def _evaluate_range(
    name: str,
    value: float,
    lo: float,
    hi: float,
    near_margin: float,
) -> tuple[ParameterMargin, List[str]]:
    """Evaluate a parameter with a [lo, hi] operating range."""
    violations: List[str] = []
    span = hi - lo
    if span <= 0:
        # Degenerate range — can't evaluate
        return ParameterMargin(
            name=name, value=value, lower_limit=lo, upper_limit=hi,
            margin=1.0, status="OK",
        ), violations

    near_band = span * near_margin

    if value < lo:
        dist = lo - value
        margin = -(dist / span)
        violations.append(f"{name}_LOW")
        status: ParameterStatus = "OUTSIDE"
    elif value > hi:
        dist = value - hi
        margin = -(dist / span)
        violations.append(f"{name}_HIGH")
        status = "OUTSIDE"
    else:
        dist_to_lo = value - lo
        dist_to_hi = hi - value
        nearest = min(dist_to_lo, dist_to_hi)
        margin = nearest / span

        if nearest < near_band:
            status = "NEAR_LIMIT"
            if dist_to_lo < near_band:
                violations.append(f"{name}_NEAR_LOW")
            if dist_to_hi < near_band:
                violations.append(f"{name}_NEAR_HIGH")
        else:
            status = "OK"

    return ParameterMargin(
        name=name, value=round(value, 4), lower_limit=lo, upper_limit=hi,
        margin=round(margin, 4), status=status,
    ), violations


def _evaluate_threshold(
    name: str,
    value: float,
    warn: float,
    critical: float,
) -> tuple[ParameterMargin, List[str]]:
    """Evaluate a parameter against warn / critical thresholds (upper only)."""
    violations: List[str] = []

    if critical <= 0:
        margin = 1.0
        status: ParameterStatus = "OK"
    elif value > critical:
        margin = -(value - critical) / critical
        status = "OUTSIDE"
        violations.append(f"{name}_CRITICAL")
    elif value > warn:
        margin = (critical - value) / critical
        status = "NEAR_LIMIT"
        violations.append(f"{name}_WARN")
    else:
        margin = (critical - value) / critical
        status = "OK"

    return ParameterMargin(
        name=name, value=round(value, 4),
        lower_limit=None, upper_limit=critical,
        margin=round(max(-1.0, min(1.0, margin)), 4), status=status,
    ), violations


# ─── Main Evaluation Function ─────────────────────────────────────────────────

def evaluate_envelope(
    wob: float,
    rpm: float,
    torque: float,
    vibration: float,
    dls: float,
    inclination: float,
    config: PeteConfig,
    formation_class: Optional[str] = None,
) -> PeteEnvelopeResult:
    """
    Evaluate drilling parameters against the operating envelope.

    Returns a structured result with per-parameter margins, violation codes,
    steering aggressiveness restriction, and formation sensitivity.
    """
    # ── Formation sensitivity ─────────────────────────────────────────────
    formation = _classify_formation(formation_class)
    mult = config.formation_multipliers.get(formation, 1.0)

    # Apply formation multiplier to *max* thresholds
    adj_wob_max = config.wob_max * mult
    adj_rpm_max = config.rpm_max * mult
    adj_torque_max = config.torque_max * mult
    adj_vib_warn = config.vibration_warn * mult
    adj_vib_critical = config.vibration_critical * mult
    adj_dls_warn = config.dls_warn * mult
    adj_dls_critical = config.dls_critical * mult
    adj_incl_max = config.inclination_max  # not formation-sensitive

    near = config.near_limit_margin
    all_margins: List[ParameterMargin] = []
    all_violations: List[str] = []

    # ── Ranged parameters ─────────────────────────────────────────────────
    for name, val, lo, hi in [
        ("WOB", wob, config.wob_min, adj_wob_max),
        ("RPM", rpm, config.rpm_min, adj_rpm_max),
        ("TORQUE", torque, config.torque_min, adj_torque_max),
    ]:
        pm, vs = _evaluate_range(name, val, lo, hi, near)
        all_margins.append(pm)
        all_violations.extend(vs)

    # ── Threshold parameters ──────────────────────────────────────────────
    for name, val, warn, crit in [
        ("VIBRATION", vibration, adj_vib_warn, adj_vib_critical),
        ("DLS", dls, adj_dls_warn, adj_dls_critical),
    ]:
        pm, vs = _evaluate_threshold(name, val, warn, crit)
        all_margins.append(pm)
        all_violations.extend(vs)

    # ── Inclination ───────────────────────────────────────────────────────
    if adj_incl_max > 0:
        pm, vs = _evaluate_threshold("INCLINATION", inclination, adj_incl_max * 0.85, adj_incl_max)
        all_margins.append(pm)
        all_violations.extend(vs)

    # ── Overall status ────────────────────────────────────────────────────
    statuses = [m.status for m in all_margins]
    if "OUTSIDE" in statuses:
        overall: OverallStatus = "OUTSIDE_LIMITS"
    elif "NEAR_LIMIT" in statuses:
        overall = "NEAR_LIMIT"
    else:
        overall = "WITHIN_LIMITS"

    # ── Steering aggressiveness restriction ───────────────────────────────
    base_dls_room = max(0.0, adj_dls_critical - dls)
    if overall == "OUTSIDE_LIMITS":
        max_dls_change = 0.0
    elif overall == "NEAR_LIMIT":
        max_dls_change = round(base_dls_room * 0.5, 4)
    else:
        max_dls_change = round(base_dls_room, 4)

    # Strip NEAR_* warnings from violations list — keep only actionable codes
    actionable_violations = [v for v in all_violations if "NEAR_" not in v]

    return PeteEnvelopeResult(
        overall_status=overall,
        parameter_margins=all_margins,
        violations=actionable_violations if actionable_violations else all_violations,
        max_dls_change=max_dls_change,
        formation_sensitivity=formation,
    )
