from dataclasses import dataclass
from typing import Tuple

from verifier.verification_report import IndependentVerificationReport


@dataclass(frozen=True)
class RegisteredArtifact:
    """One immutable artifact admitted to the registration record."""

    artifact_type: str
    artifact_id: str


@dataclass(frozen=True)
class ArtifactRegistration:
    """
    Immutable registration record for one verified REOS transition.

    Registration records which artifacts were admitted.
    It does not modify, certify, or reinterpret those artifacts.
    """

    registration_id: str
    transition_id: str
    verification_report_id: str
    artifacts: Tuple[RegisteredArtifact, ...]


def register_verified_artifacts(
    report: IndependentVerificationReport,
    telemetry_trace_id: str,
) -> ArtifactRegistration:
    """
    Register artifacts only after successful independent verification.
    """
    if not report.verified:
        raise ValueError(
            "Unverified execution artifacts cannot be registered."
        )

    artifacts = (
        RegisteredArtifact(
            artifact_type="recognition_result",
            artifact_id=report.recognition_id,
        ),
        RegisteredArtifact(
            artifact_type="transition_telemetry",
            artifact_id=telemetry_trace_id,
        ),
        RegisteredArtifact(
            artifact_type="independent_verification_report",
            artifact_id=report.report_id,
        ),
    )

    registration_material = "|".join(
        [
            report.transition_id,
            report.report_id,
            *(
                f"{artifact.artifact_type}:{artifact.artifact_id}"
                for artifact in artifacts
            ),
        ]
    )

    # Local import keeps registration independent of runtime modules.
    import hashlib

    registration_digest = hashlib.sha256(
        registration_material.encode("utf-8")
    ).hexdigest()

    return ArtifactRegistration(
        registration_id=(
            f"AR-{registration_digest[:16].upper()}"
        ),
        transition_id=report.transition_id,
        verification_report_id=report.report_id,
        artifacts=artifacts,
    )
