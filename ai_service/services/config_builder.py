"""
Config derivation helpers.
Build Limits and PeteConfig objects from raw DB config dicts.
"""

from schemas import Limits
from pete_envelope import PeteConfig


def cfg_float(raw_config: dict, key: str, default=0.0) -> float:
    """Unwrap config value — DB stores JSON dicts like {"value": X}."""
    v = raw_config.get(key, default)
    if isinstance(v, dict):
        return float(v.get("value", default))
    return float(v)


def build_limits(raw_config: dict) -> Limits:
    """Build Limits object from raw config dict, handling nested JSON values."""
    c = lambda key, default=0.0: cfg_float(raw_config, key, default)
    return Limits(
        confidence_reject_threshold=c("alert_threshold_critical", 0.3),
        confidence_reduce_threshold=c("alert_threshold_high", 0.5),
        dls_reject_threshold=c("dls_reject_threshold", 3.0),
        dls_reduce_threshold=c("dls_reduce_threshold", 2.0),
        vibration_reject_threshold=c("vibration_reject_threshold", 0.5),
        vibration_reduce_threshold=c("vibration_reduce_threshold", 0.3),
        max_vibration_g=c("max_vibration_g", 0.5),
        max_dls_deg_100ft=c("max_dls_deg_100ft", 3.0),
        wob_range=[c("wob_min", 20), c("wob_max", 60)],
        torque_range=[c("torque_min", 0), c("torque_max", 50)],
        rpm_range=[c("rpm_min", 50), c("rpm_max", 300)],
    )


def build_pete_config(raw_config: dict) -> PeteConfig:
    """Build PeteConfig from raw DB config, falling back to defaults."""
    c = lambda key, default: cfg_float(raw_config, key, default)
    return PeteConfig(
        wob_min=c("pete_wob_min", 20.0),
        wob_max=c("pete_wob_max", 60.0),
        rpm_min=c("pete_rpm_min", 50.0),
        rpm_max=c("pete_rpm_max", 300.0),
        torque_min=c("pete_torque_min", 0.0),
        torque_max=c("pete_torque_max", 50.0),
        vibration_warn=c("pete_vibration_warn", 0.35),
        vibration_critical=c("pete_vibration_critical", 0.5),
        dls_warn=c("pete_dls_warn", 2.5),
        dls_critical=c("pete_dls_critical", 3.0),
        inclination_max=c("pete_inclination_max", 90.0),
        near_limit_margin=c("pete_near_limit_margin", 0.15),
        formation_multipliers={
            "soft": c("pete_formation_mult_soft", 0.8),
            "medium": c("pete_formation_mult_medium", 1.0),
            "hard": c("pete_formation_mult_hard", 1.2),
        },
    )
