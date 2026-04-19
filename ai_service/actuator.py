"""
Virtual Actuator module for simulating RSS (Rotary Steerable System) command execution.

Pipeline position: telemetry → model → safety gate → **actuator**

The actuator receives commands from the decision pipeline and simulates
execution, maintaining its own state machine. In SIMULATION mode all
executions are virtual; in PROTOTYPE mode the interface is ready for
real hardware integration.

State is persisted to a JSON file so fault/manual overrides survive
backend restarts.
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import threading
import json
import os


# Persistence file lives next to the database
_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "actuator_state.json")


class ActuatorState(str, Enum):
    """Actuator hardware state machine."""
    IDLE = "IDLE"
    COMPLETE = "COMPLETE"
    FAULT = "FAULT"
    MANUAL = "MANUAL"


class ActuatorOutcome(str, Enum):
    """Outcome of an actuator command execution."""
    ACK_EXECUTED = "ACK_EXECUTED"
    ACK_REDUCED = "ACK_REDUCED"
    ACK_REJECTED = "ACK_REJECTED"
    ACK_BLOCKED = "ACK_BLOCKED"
    ACK_MANUAL_FALLBACK = "ACK_MANUAL_FALLBACK"


@dataclass
class ActuatorResponse:
    """Result returned by the actuator after processing a command."""
    outcome: ActuatorOutcome
    state: ActuatorState
    last_command: str
    timestamp: str
    message: str
    is_simulated: bool


class VirtualActuator:
    """
    Stateful virtual actuator that simulates RSS command execution.

    Thread-safe: all state mutations are guarded by a lock so the
    actuator can be called from concurrent async request handlers.

    Fault and manual-override states are persisted to disk so they
    survive backend restarts — an operator who sets MANUAL override
    expects it to stick until they explicitly clear it.
    """

    def __init__(self, derate_threshold: float = 0.65):
        self._lock = threading.Lock()
        self._state: ActuatorState = ActuatorState.IDLE
        self._last_command: Optional[str] = None
        self._last_outcome: Optional[ActuatorOutcome] = None
        self._last_timestamp: Optional[str] = None
        self._last_is_simulated: bool = True
        self._fault_reason: Optional[str] = None
        self._derate_threshold = derate_threshold
        self._command_count: int = 0

        # Restore persisted override state (fault / manual) from disk
        self._restore_state()

    # ------------------------------------------------------------------
    # Command execution
    # ------------------------------------------------------------------

    def execute(
        self,
        command: str,
        gate_outcome: str,
        confidence: float,
        system_mode: str = "SIMULATION",
    ) -> ActuatorResponse:
        """
        Execute (or simulate) an RSS steering command.

        The actuator inspects the gate decision and its own state to
        determine the appropriate outcome:

        1. FAULT / MANUAL → ACK_MANUAL_FALLBACK (safe state)
        2. Gate REJECTED   → ACK_BLOCKED (no action taken)
        3. Gate REDUCED or low confidence → ACK_REDUCED (derated execution)
        4. Gate ACCEPTED   → ACK_EXECUTED (full execution)
        """
        with self._lock:
            now = datetime.utcnow().isoformat()
            is_simulated = system_mode != "PROTOTYPE"

            # --- Fault / Manual override ---
            if self._state == ActuatorState.FAULT:
                return self._respond(
                    outcome=ActuatorOutcome.ACK_MANUAL_FALLBACK,
                    state=ActuatorState.FAULT,
                    command=command,
                    timestamp=now,
                    message=f"Actuator in FAULT state ({self._fault_reason}). Command held — manual fallback active.",
                    is_simulated=is_simulated,
                )

            if self._state == ActuatorState.MANUAL:
                return self._respond(
                    outcome=ActuatorOutcome.ACK_MANUAL_FALLBACK,
                    state=ActuatorState.MANUAL,
                    command=command,
                    timestamp=now,
                    message="Operator manual override active. Automatic commands suspended.",
                    is_simulated=is_simulated,
                )

            # --- Gate blocked ---
            if gate_outcome == "REJECTED":
                return self._respond(
                    outcome=ActuatorOutcome.ACK_BLOCKED,
                    state=ActuatorState.IDLE,
                    command=command,
                    timestamp=now,
                    message="Safety gate rejected command. No actuator action taken.",
                    is_simulated=is_simulated,
                )

            # --- Derated execution ---
            if gate_outcome == "REDUCED" or confidence < self._derate_threshold:
                reason = (
                    "gate derate" if gate_outcome == "REDUCED"
                    else f"low confidence ({confidence:.2f} < {self._derate_threshold})"
                )
                return self._respond(
                    outcome=ActuatorOutcome.ACK_REDUCED,
                    state=ActuatorState.COMPLETE,
                    command=command,
                    timestamp=now,
                    message=f"Command executed at reduced parameters ({reason}).",
                    is_simulated=is_simulated,
                )

            # --- Full execution ---
            return self._respond(
                outcome=ActuatorOutcome.ACK_EXECUTED,
                state=ActuatorState.COMPLETE,
                command=command,
                timestamp=now,
                message="Command executed successfully.",
                is_simulated=is_simulated,
            )

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def enter_fault(self, reason: str) -> None:
        """Put actuator into FAULT state. All commands → ACK_MANUAL_FALLBACK."""
        with self._lock:
            self._state = ActuatorState.FAULT
            self._fault_reason = reason
            self._persist_state()

    def clear_fault(self) -> None:
        """Clear FAULT state, return to IDLE."""
        with self._lock:
            if self._state == ActuatorState.FAULT:
                self._state = ActuatorState.IDLE
                self._fault_reason = None
                self._persist_state()

    def enter_manual(self) -> None:
        """Operator override — suspend automatic commands."""
        with self._lock:
            self._state = ActuatorState.MANUAL
            self._persist_state()

    def clear_manual(self) -> None:
        """Release operator override, return to IDLE."""
        with self._lock:
            if self._state == ActuatorState.MANUAL:
                self._state = ActuatorState.IDLE
                self._persist_state()

    def get_status(self) -> dict:
        """Return a serialisable snapshot of actuator state."""
        with self._lock:
            return {
                "state": self._state.value,
                "last_command": self._last_command,
                "last_outcome": self._last_outcome.value if self._last_outcome else None,
                "timestamp": self._last_timestamp,
                "is_simulated": self._last_is_simulated,
                "fault_reason": self._fault_reason,
                "command_count": self._command_count,
            }

    # ------------------------------------------------------------------
    # Persistence — only override states (FAULT / MANUAL) are saved
    # ------------------------------------------------------------------

    def _persist_state(self) -> None:
        """Write override state to disk. Called under lock."""
        data = {
            "state": self._state.value,
            "fault_reason": self._fault_reason,
        }
        try:
            with open(_STATE_FILE, "w") as f:
                json.dump(data, f)
        except OSError:
            pass  # Best-effort — don't crash the actuator

    def _restore_state(self) -> None:
        """Load persisted override state from disk on startup."""
        try:
            with open(_STATE_FILE, "r") as f:
                data = json.load(f)
            saved_state = data.get("state")
            if saved_state == ActuatorState.FAULT.value:
                self._state = ActuatorState.FAULT
                self._fault_reason = data.get("fault_reason")
            elif saved_state == ActuatorState.MANUAL.value:
                self._state = ActuatorState.MANUAL
            # Other states (IDLE, COMPLETE, EXECUTING) don't need restoring
        except (OSError, json.JSONDecodeError, KeyError):
            pass  # No saved state or corrupt file — start fresh

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _respond(
        self,
        outcome: ActuatorOutcome,
        state: ActuatorState,
        command: str,
        timestamp: str,
        message: str,
        is_simulated: bool,
    ) -> ActuatorResponse:
        """Build response and persist state."""
        self._state = state
        self._last_command = command
        self._last_outcome = outcome
        self._last_timestamp = timestamp
        self._last_is_simulated = is_simulated
        self._command_count += 1

        return ActuatorResponse(
            outcome=outcome,
            state=state,
            last_command=command,
            timestamp=timestamp,
            message=message,
            is_simulated=is_simulated,
        )


# Module-level singleton — shared across all request handlers
virtual_actuator = VirtualActuator()
