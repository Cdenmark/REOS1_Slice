from verifier.artifact_registration import (
    register_verified_artifacts,
)
from verifier.verification_report import (
    IndependentVerificationReport,
    VerificationCheck,
)


def make_report() -> IndependentVerificationReport:
    return IndependentVerificationReport(
        report_id="VR-001",
        verifier_version="clean-room-0.1.0",
        transition_id="TRN-001",
        recognition_id="RR-001",
        verified=True,
        checks=(
            VerificationCheck(
                check_name="recognition_id",
                passed=True,
            ),
        ),
    )


def test_verified_artifacts_can_be_registered():
    registration = register_verified_artifacts(
        report=make_report(),
        telemetry_trace_id="TRACE-TRN-001",
    )

    assert registration.registration_id.startswith("AR-")
    assert registration.transition_id == "TRN-001"
    assert registration.verification_report_id == "VR-001"
    assert [
        artifact.artifact_type
        for artifact in registration.artifacts
    ] == [
        "recognition_result",
        "transition_telemetry",
        "independent_verification_report",
    ]


def test_artifact_registration_is_reproducible():
    first = register_verified_artifacts(
        report=make_report(),
        telemetry_trace_id="TRACE-TRN-001",
    )

    second = register_verified_artifacts(
        report=make_report(),
        telemetry_trace_id="TRACE-TRN-001",
    )

    assert first == second
    assert first.registration_id == second.registration_id
