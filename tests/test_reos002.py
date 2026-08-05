import pytest

from contracts.transition_contract import (
    AuthorityMetadata,
    TransitionContract,
)
from runtime.executor import ConstitutionalViolationError
from runtime.ingress_payload import GovernedIngressPayload
from runtime.reos002 import REOS002Runtime


ALL_OPERATIONS = [
    "ingress_hash",
    "instantiate_recognition_unit",
    "generate_candidate_basins",
    "evaluate_candidate_basins",
    "determine_primary_basin",
    "record_rejected_basins",
    "assemble_recognition_result",
    "emit_transition_telemetry",
]


def make_contract(
    allowed_operations: list[str] | None = None,
) -> TransitionContract:
    return TransitionContract(
        contract_id="CONTRACT-REOS-002",
        transition_id="REOS-002",
        authority=AuthorityMetadata(
            declaration_id="REOS-002",
            declaration_hash="a" * 64,
            compiler_release="compiler-0.2.0",
            compiler_digest="b" * 64,
            generated_at="2026-08-04T22:00:00+00:00",
        ),
        constitution_version="2.0.0",
        contract_version="2.0.0",
        allowed_operations=(
            ALL_OPERATIONS
            if allowed_operations is None
            else allowed_operations
        ),
        permitted_exports=[
            "recognition_result",
            "transition_telemetry",
            "candidate_basin_evaluation",
        ],
        prohibited_exports=[
            "activate_seam",
            "remedy_selection",
            "protocol_generation",
        ],
        operation_parameters={},
    )


def make_payload() -> GovernedIngressPayload:
    return GovernedIngressPayload(
        payload_id="ING-002",
        raw_observation="My system won't shut off.",
        source_type="user_report",
    )


def test_reos002_executes_complete_multi_basin_pipeline():
    result, telemetry = REOS002Runtime().execute(
        contract=make_contract(),
        payload=make_payload(),
    )

    assert result.orientation.primary_basin == "REC-002"
    assert result.resolution_state == "oriented"

    assert telemetry.candidate_basins == [
        "REC-002",
        "REC-007",
    ]

    assert telemetry.selected_basin == "REC-002"
    assert len(telemetry.rejected_basins) == 1
    assert telemetry.rejected_basins[0].basin_id == "REC-007"

    assert telemetry.termination_reason == (
        "MULTI_BASIN_ORIENTATION_SUCCESS"
    )


def test_reos002_execution_is_reproducible():
    runtime = REOS002Runtime()
    contract = make_contract()
    payload = make_payload()

    first_result, first_telemetry = runtime.execute(
        contract=contract,
        payload=payload,
    )

    second_result, second_telemetry = runtime.execute(
        contract=contract,
        payload=payload,
    )

    assert first_result == second_result
    assert first_telemetry == second_telemetry


def test_reos002_fails_closed_when_stage_is_unauthorized():
    allowed_operations = [
        operation
        for operation in ALL_OPERATIONS
        if operation != "evaluate_candidate_basins"
    ]

    with pytest.raises(
        ConstitutionalViolationError,
        match="Unauthorized operation",
    ):
        REOS002Runtime().execute(
            contract=make_contract(
                allowed_operations=allowed_operations
            ),
            payload=make_payload(),
        )