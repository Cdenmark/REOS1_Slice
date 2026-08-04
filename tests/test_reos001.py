import pytest

from contracts.transition_contract import (
    AuthorityMetadata,
    TransitionContract,
)
from runtime.executor import ConstitutionalViolationError
from runtime.ingress_payload import GovernedIngressPayload
from runtime.reos001 import REOS001Runtime


def make_contract(
    allowed_operations: list[str] | None = None,
) -> TransitionContract:
    if allowed_operations is None:
        allowed_operations = [
            "ingress_hash",
            "instantiate_recognition_unit",
            "determine_primary_basin",
        ]

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
        allowed_operations=allowed_operations,
        permitted_exports=[
            "recognition_result",
            "transition_telemetry",
        ],
        prohibited_exports=[
            "remedy_selection",
            "protocol_generation",
        ],
    )


def make_payload() -> GovernedIngressPayload:
    return GovernedIngressPayload(
        payload_id="ING-001",
        raw_observation="My system won't shut off.",
        source_type="user_report",
    )


def test_reos001_executes_end_to_end():
    result, telemetry = REOS001Runtime().execute(
        contract=make_contract(),
        payload=make_payload(),
    )

    assert result.orientation.primary_basin == "REC-002"
    assert result.resolution_state == "oriented"

    assert telemetry.selected_basin == "REC-002"
    assert telemetry.transition_id.startswith("TRN-")
    assert telemetry.lineage is not None
    assert telemetry.lineage.parent_artifacts == [
        make_payload().digest(),
        make_contract().digest(),
    ]


def test_reos001_is_reproducible():
    runtime = REOS001Runtime()

    first_result, first_telemetry = runtime.execute(
        contract=make_contract(),
        payload=make_payload(),
    )

    second_result, second_telemetry = runtime.execute(
        contract=make_contract(),
        payload=make_payload(),
    )

    assert first_result == second_result
    assert first_telemetry == second_telemetry


def test_reos001_fails_closed_without_operation_authority():
    with pytest.raises(
        ConstitutionalViolationError,
        match="Unauthorized operation",
    ):
        REOS001Runtime().execute(
            contract=make_contract(
                allowed_operations=[
                    "ingress_hash",
                    "instantiate_recognition_unit",
                ]
            ),
            payload=make_payload(),
        )
