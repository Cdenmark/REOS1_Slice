from contracts.transition_contract import (
    AuthorityMetadata,
    TransitionContract,
)
from runtime.ingress_payload import GovernedIngressPayload
from runtime.reos001 import REOS001Runtime
from verifier.artifact_registration import register_verified_artifacts
from verifier.clean_room import create_verification_report
from verifier.provenance_certificate import certify_provenance


def make_contract() -> TransitionContract:
    return TransitionContract(
        contract_id="CONTRACT-REOS-001",
        transition_id="REOS-001",
        authority=AuthorityMetadata(
            declaration_id="REOS-001",
            declaration_hash="a" * 64,
            compiler_release="compiler-0.1.0",
            compiler_digest="b" * 64,
            generated_at="2026-08-04T18:00:00+00:00",
        ),
        constitution_version="2.0.0",
        contract_version="1.0.0",
        allowed_operations=[
            "ingress_hash",
            "instantiate_recognition_unit",
            "determine_primary_basin",
        ],
        permitted_exports=[
            "recognition_result",
            "transition_telemetry",
        ],
        prohibited_exports=[
            "remedy_selection",
            "protocol_generation",
        ],
        operation_parameters={},
    )


def make_payload() -> GovernedIngressPayload:
    return GovernedIngressPayload(
        payload_id="ING-001",
        raw_observation="My system won't shut off.",
        source_type="user_report",
    )


def test_reos001_reaches_constitutional_closure():
    contract = make_contract()
    payload = make_payload()

    result, telemetry = REOS001Runtime().execute(
        contract=contract,
        payload=payload,
    )

    report = create_verification_report(
        contract=contract,
        payload=payload,
        result=result,
        telemetry=telemetry,
    )

    registration = register_verified_artifacts(
        report=report,
        telemetry_trace_id=telemetry.trace_id,
    )

    certificate = certify_provenance(
        registration=registration,
        report=report,
    )

    assert result.orientation.primary_basin == "REC-002"

    assert telemetry.transition_id == report.transition_id
    assert report.recognition_id == result.recognition_id

    assert registration.transition_id == telemetry.transition_id
    assert registration.verification_report_id == report.report_id

    assert certificate.transition_id == telemetry.transition_id
    assert certificate.registration_id == registration.registration_id
    assert certificate.verification_report_id == report.report_id
    assert certificate.status == "CERTIFIED"
