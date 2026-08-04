from verifier.verification_report import (
    IndependentVerificationReport,
    VerificationCheck,
)


def test_independent_verification_report_creation():
    report = IndependentVerificationReport(
        report_id="VR-001",
        verifier_version="clean-room-0.1.0",
        transition_id="TRN-001",
        recognition_id="RR-001",
        verified=True,
        checks=(
            VerificationCheck(
                check_name="transition_id",
                passed=True,
            ),
            VerificationCheck(
                check_name="recognition_id",
                passed=True,
            ),
        ),
    )

    assert report.verified is True
    assert report.checks[0].check_name == "transition_id"
    assert all(check.passed for check in report.checks)
