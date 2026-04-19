"""
Unit tests for core business logic functions.
Tests safety gate, confidence calculation, recommendation logic.
"""

import pytest
from services.prediction import (
    calculate_recommendation,
    calculate_confidence,
    determine_gate_status,
    determine_gate_status_config,
    get_event_tags,
)
from schemas import Limits


class TestCalculateRecommendation:
    """Unit tests for calculate_recommendation() function."""

    def test_hold_when_dls_exceeds_6(self):
        """Test that DLS > 6 returns 'Hold'."""
        result = calculate_recommendation(dls=6.5, inclination=20, vibration=1.0)
        assert result == "Hold"

    def test_drop_when_inclination_exceeds_45(self):
        """Test that inclination > 45 returns 'Drop' (if DLS <= 6)."""
        result = calculate_recommendation(dls=5.0, inclination=50, vibration=1.0)
        assert result == "Drop"

    def test_build_for_normal_conditions(self):
        """Test that normal conditions return 'Build'."""
        result = calculate_recommendation(dls=4.0, inclination=30, vibration=1.0)
        assert result == "Build"

    def test_dls_takes_priority_over_inclination(self):
        """Test that high DLS returns 'Hold' even with low inclination."""
        result = calculate_recommendation(dls=7.0, inclination=30, vibration=1.0)
        assert result == "Hold"

    def test_boundary_dls_at_6(self):
        """Test boundary condition at DLS = 6."""
        result = calculate_recommendation(dls=6.0, inclination=30, vibration=1.0)
        # At DLS=6 (not > 6), return Build
        assert result == "Build"

    def test_boundary_dls_just_above_6(self):
        """Test boundary condition just above DLS = 6."""
        result = calculate_recommendation(dls=6.01, inclination=30, vibration=1.0)
        # Just above DLS=6, should return Hold
        assert result == "Hold"

    def test_boundary_dls_below_6(self):
        """Test boundary condition just below DLS = 6."""
        result = calculate_recommendation(dls=5.99, inclination=30, vibration=1.0)
        assert result == "Build"


class TestCalculateConfidence:
    """Unit tests for calculate_confidence() function."""

    def test_base_confidence_is_0_95(self):
        """Test base confidence score with ideal conditions."""
        result = calculate_confidence(dls=2.0, vibration=0.5, torque=15000)
        assert result == 0.95

    def test_confidence_decreases_with_dls(self):
        """Test that DLS > 4 reduces confidence."""
        result_high_dls = calculate_confidence(dls=5.0, vibration=0.5, torque=15000)
        result_low_dls = calculate_confidence(dls=2.0, vibration=0.5, torque=15000)
        assert result_high_dls < result_low_dls

    def test_confidence_decreases_with_vibration(self):
        """Test that vibration > 2 reduces confidence."""
        result_high_vib = calculate_confidence(dls=2.0, vibration=2.5, torque=15000)
        result_low_vib = calculate_confidence(dls=2.0, vibration=0.5, torque=15000)
        assert result_high_vib < result_low_vib

    def test_confidence_decreases_with_extreme_torque(self):
        """Test that torque outside acceptable range reduces confidence."""
        result_low_torque = calculate_confidence(dls=2.0, vibration=0.5, torque=3000)
        result_normal_torque = calculate_confidence(dls=2.0, vibration=0.5, torque=15000)
        result_high_torque = calculate_confidence(dls=2.0, vibration=0.5, torque=40000)
        assert result_low_torque < result_normal_torque
        assert result_high_torque < result_normal_torque

    def test_confidence_is_bounded(self):
        """Test that confidence is always between 0.55 and 0.95."""
        # Test extreme high values
        result_extreme = calculate_confidence(dls=10.0, vibration=5.0, torque=50000)
        assert 0.55 <= result_extreme <= 0.95

        # Test normal values
        result_normal = calculate_confidence(dls=3.0, vibration=1.0, torque=15000)
        assert 0.55 <= result_normal <= 0.95

    def test_confidence_does_not_exceed_0_95(self):
        """Test that confidence never exceeds 0.95."""
        result = calculate_confidence(dls=1.0, vibration=0.1, torque=15000)
        assert result <= 0.95


class TestDetermineGateStatus:
    """Unit tests for determine_gate_status() function."""

    def test_rejected_when_confidence_low(self):
        """Test rejection when confidence < 0.6."""
        status, reason = determine_gate_status(confidence=0.55, dls=4.0, vibration=1.0)
        assert status == "REJECTED"
        assert reason == "LOW_CONFIDENCE"

    def test_rejected_when_dls_exceeds_8(self):
        """Test rejection when DLS > 8."""
        status, reason = determine_gate_status(confidence=0.75, dls=8.5, vibration=1.0)
        assert status == "REJECTED"
        assert reason == "LIMIT_EXCEEDED"

    def test_reduced_when_dls_high_but_below_reject(self):
        """Test 'REDUCED' when DLS >= 6 but <= 8."""
        status, reason = determine_gate_status(confidence=0.75, dls=6.5, vibration=1.0)
        assert status == "REDUCED"
        assert reason is None

    def test_reduced_when_vibration_exceeds_3(self):
        """Test 'REDUCED' when vibration > 3."""
        status, reason = determine_gate_status(confidence=0.75, dls=4.0, vibration=3.5)
        assert status == "REDUCED"
        assert reason is None

    def test_accepted_for_safe_conditions(self):
        """Test 'ACCEPTED' for normal conditions."""
        status, reason = determine_gate_status(confidence=0.80, dls=4.0, vibration=1.0)
        assert status == "ACCEPTED"
        assert reason is None

    def test_boundary_dls_at_6(self):
        """Test boundary condition at DLS = 6 (should be REDUCED)."""
        status, _ = determine_gate_status(confidence=0.75, dls=6.0, vibration=1.0)
        assert status == "REDUCED"

    def test_boundary_confidence_at_0_6(self):
        """Test boundary condition at confidence = 0.6 (should be ACCEPTED)."""
        status, _ = determine_gate_status(confidence=0.6, dls=4.0, vibration=1.0)
        # At confidence=0.6 (not < 0.6), should be ACCEPTED since dls and vibration are safe
        assert status == "ACCEPTED"

    def test_boundary_confidence_just_below_0_6(self):
        """Test boundary condition just below confidence = 0.6."""
        status, _ = determine_gate_status(confidence=0.59, dls=4.0, vibration=1.0)
        # Just below confidence=0.6, should be REJECTED
        assert status == "REJECTED"


class TestDetermineGateStatusConfig:
    """Unit tests for determine_gate_status_config() using custom limits."""

    @pytest.fixture
    def custom_limits(self):
        """Custom limits fixture."""
        return Limits(
            confidence_reject_threshold=0.65,
            confidence_reduce_threshold=0.70,
            dls_reject_threshold=7.5,
            dls_reduce_threshold=5.5,
            vibration_reject_threshold=2.5,
            vibration_reduce_threshold=2.0,
            max_vibration_g=4.0,
            max_dls_deg_100ft=10.0,
            wob_range=[20.0, 100.0],
            torque_range=[5000.0, 50000.0],
            rpm_range=[50.0, 200.0],
        )

    def test_rejected_when_confidence_below_threshold(self, custom_limits):
        """Test rejection when confidence below custom threshold."""
        status, reason = determine_gate_status_config(
            confidence=0.60, dls=4.0, vibration=1.0, limits=custom_limits
        )
        assert status == "REJECTED"
        assert reason == "LOW_CONFIDENCE"

    def test_rejected_when_dls_above_threshold(self, custom_limits):
        """Test rejection when DLS above custom reject threshold."""
        status, reason = determine_gate_status_config(
            confidence=0.75, dls=8.0, vibration=1.0, limits=custom_limits
        )
        assert status == "REJECTED"
        assert reason == "DLS_LIMIT_EXCEEDED"

    def test_rejected_when_vibration_above_threshold(self, custom_limits):
        """Test rejection when vibration above custom reject threshold."""
        status, reason = determine_gate_status_config(
            confidence=0.75, dls=4.0, vibration=3.0, limits=custom_limits
        )
        assert status == "REJECTED"
        assert reason == "VIBRATION_LIMIT_EXCEEDED"

    def test_reduced_when_dls_between_thresholds(self, custom_limits):
        """Test REDUCED when DLS between reduce and reject thresholds."""
        status, _ = determine_gate_status_config(
            confidence=0.75, dls=6.0, vibration=1.0, limits=custom_limits
        )
        assert status == "REDUCED"

    def test_reduced_when_vibration_between_thresholds(self, custom_limits):
        """Test REDUCED when vibration between reduce and reject thresholds."""
        status, _ = determine_gate_status_config(
            confidence=0.75, dls=4.0, vibration=2.2, limits=custom_limits
        )
        assert status == "REDUCED"

    def test_accepted_when_all_below_reduce_thresholds(self, custom_limits):
        """Test ACCEPTED when all values below reduce thresholds."""
        status, _ = determine_gate_status_config(
            confidence=0.80, dls=5.0, vibration=1.5, limits=custom_limits
        )
        assert status == "ACCEPTED"

    def test_reason_priority_confidence_over_dls(self, custom_limits):
        """Test that LOW_CONFIDENCE is reported first if multiple rejections."""
        status, reason = determine_gate_status_config(
            confidence=0.60, dls=8.0, vibration=3.0, limits=custom_limits
        )
        assert status == "REJECTED"
        assert reason == "LOW_CONFIDENCE"  # Confidence is checked first


class TestGetEventTags:
    """Unit tests for get_event_tags() function."""

    def test_high_dls_tag_when_dls_exceeds_6(self):
        """Test that high_dls tag added when DLS > 6."""
        tags = get_event_tags(dls=6.5, vibration=1.0, confidence=0.80)
        assert "high_dls" in tags

    def test_high_dls_tag_not_added_when_dls_low(self):
        """Test that high_dls tag not added when DLS <= 6."""
        tags = get_event_tags(dls=5.0, vibration=1.0, confidence=0.80)
        assert "high_dls" not in tags

    def test_high_vibration_tag_when_vibration_exceeds_3(self):
        """Test that high_vibration tag added when vibration > 3."""
        tags = get_event_tags(dls=4.0, vibration=3.5, confidence=0.80)
        assert "high_vibration" in tags

    def test_high_vibration_tag_not_added_when_vibration_low(self):
        """Test that high_vibration tag not added when vibration <= 3."""
        tags = get_event_tags(dls=4.0, vibration=2.5, confidence=0.80)
        assert "high_vibration" not in tags

    def test_low_confidence_tag_when_confidence_below_0_7(self):
        """Test that low_confidence tag added when confidence < 0.7."""
        tags = get_event_tags(dls=4.0, vibration=1.0, confidence=0.65)
        assert "low_confidence" in tags

    def test_low_confidence_tag_not_added_when_confidence_high(self):
        """Test that low_confidence tag not added when confidence >= 0.7."""
        tags = get_event_tags(dls=4.0, vibration=1.0, confidence=0.75)
        assert "low_confidence" not in tags

    def test_multiple_tags_for_high_risk_conditions(self):
        """Test multiple tags when multiple conditions triggered."""
        tags = get_event_tags(dls=7.0, vibration=3.5, confidence=0.60)
        assert "high_dls" in tags
        assert "high_vibration" in tags
        assert "low_confidence" in tags

    def test_no_tags_for_safe_conditions(self):
        """Test no tags for safe conditions."""
        tags = get_event_tags(dls=4.0, vibration=1.0, confidence=0.85)
        assert len(tags) == 0

    def test_boundary_dls_at_6(self):
        """Test boundary condition at DLS = 6 (should not trigger tag)."""
        tags = get_event_tags(dls=6.0, vibration=1.0, confidence=0.80)
        assert "high_dls" not in tags


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
