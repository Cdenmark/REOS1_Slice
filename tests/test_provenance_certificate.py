import pytest

from verifier.artifact_registration import (
    ArtifactRegistration,
    RegisteredArtifact,
)
from verifier.provenance_certificate import certify_provenance
from verifier.verification_report import (
    IndependentVerificationReport,
    VerificationCheck,
)


def make_report(
    *,
    report_id: str = "VR-001",
    transition_id: str = "TRN-001",
    verified: bool = True,
) -> IndependentVerificationReport:
    return IndependentVerificationReport(
        report_id=report_id,
        verifier_version="clean-room-0.1.0",
        transition_id=transition_id,
        recognition_id="RR-001",
        verified=verified,
        checks=(
            VerificationCheck(
                check_name="recognition_id",
                passed=verified,
            ),
        ),
    )


def make_registration() -> ArtifactRegistration:
    return ArtifactRegistration(
        registration_id="AR-001",
        transition_id="TRN-001",
        verification_report_id="VR-001",
        artifacts=(
            RegisteredArtifact(
                artifact_type="recognition_result",
                artifact_id="RR-001",
            ),
            RegisteredArtifact(
                artifact_type="transition_telemetry",
                artifact_id="TRACE-TRN-001",
            ),
            RegisteredArtifact(
                artifact_type="independent_verification_report",
                artifact_id="VR-001",
            ),
        ),
    )


def test_provenance_certificate_is_created():
    certificate = certify_provenance(
        registration=make_registration(),
        report=make_report(),
    )

    assert certificate.certificate_id.startswith("PC-")
    assert certificate.status == "CERTIFIED"
    assert certificate.transition_id == "TRN-001"
    assert len(certificate.links) == 5


def test_provenance_certificate_is_reproducible():
    first = certify_provenance(
        registration=make_registration(),
        report=make_report(),
    )

    second = certify_provenance(
        registration=make_registration(),
        report=make_report(),
    )

    assert first == second
    assert first.certificate_id == second.certificate_id


def test_provenance_certificate_rejects_failed_verification():
    with pytest.raises(
        ValueError,
        match="failed verification report",
    ):
        certify_provenance(
            registration=make_registration(),
            report=make_report(verified=False),
        )


def test_provenance_certificate_rejects_mismatched_lineage():
    with pytest.raises(
        ValueError,
        match="transition identities do not match",
    ):
        certify_provenance(
            registration=make_registration(),
            report=make_report(transition_id="TRN-DIFFERENT"),
        )
