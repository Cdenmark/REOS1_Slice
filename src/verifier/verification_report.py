from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class VerificationCheck:
    """One independently evaluated verification assertion."""

    check_name: str
    passed: bool


@dataclass(frozen=True)
class IndependentVerificationReport:
    """
    Immutable output of clean-room verification.

    This report records what the verifier established.
    It does not alter the runtime result or telemetry.
    """

    report_id: str
    verifier_version: str
    transition_id: str
    recognition_id: str
    verified: bool
    checks: Tuple[VerificationCheck, ...]
