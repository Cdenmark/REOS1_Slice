import pytest

from contracts.transition_contract import (
    AuthorityMetadata,
    TransitionContract,
)
from runtime.executor import ConstitutionalViolationError
from runtime.ingress_payload import GovernedIngressPayload
from runtime.transition_orchestrator import TransitionOrchestrator


ALL_OPERATIONS = [
    "ingress_hash",
    "instantiate_recognition_unit",
    "generate_candidate_basins",
    "evaluate_candidate_basins",
    "determine_primary_basin",
    "record_rejected_basins",
    "detect_seam_activation",
    "resolve_orientation",
    "assemble_recognition_result",
    "emit_transition_telemetry",
]


def make_contract(
    *,
    allowed_operations: list[str] | None = None,
    maximum_score_gap: float = 0.50,
) -> TransitionContract:
    return TransitionContract(
        contract_id="CONTRACT-REOS-003",
        transition_id="REOS-003",
        authority=AuthorityMetadata(
            declaration_id="REOS-003",
            declaration_hash="a" * 64,
            compiler_release="compiler-0.3.0",
            compiler_digest="b" * 64,
            generated_at="2026-08-05T18:00:00+00:00",
        ),
        constitution_version="2.0.0",
        contract_version="3.0.0",
        allowed_operations=(
            ALL_OPERATIONS
            if allowed_operations is None
            else allowed_operations
        ),
        permitted_exports=[
            "seam_aware_recognition_result",
            "transition_telemetry",
        ],
        prohibited_exports=[
            "execute_shunt",
            "remedy_selection",
            "protocol_generation",
        ],
        operation_parameters={
            "detect_seam_activation": {
                "maximum_score_gap": maximum_score_gap,
                "minimum_top_score": 0.50,
                "required_participant_count": 2,
            }
        },
    )


def make_payload() -> GovernedIngressPayload:
    return GovernedIngressPayload(
        payload_id="ING-003",
        raw_observation="My system won't shut off.",
        source_type="user_report",
    )


def test_orchestrator_executes_complete_vs003_dag():
    result, telemetry = TransitionOrchestrator().execute(
        contract=make_contract(),
        payload=make_payload(),
    )

    assert result.primary_basin == "REC-002"
    assert result.resolution_state == "SEAM_ACTIVE"
    assert result.active_seam is not None

    assert telemetry.selection_id
    assert telemetry.seam_condition_id
    assert telemetry.orientation_resolution_id
    assert telemetry.result_id == result.result_id
    assert telemetry.termination_reason == (
        "SEAM_AWARE_ORIENTATION_COMPLETE"
    )


def test_orchestrator_fails_closed_when_operation_is_unauthorized():
    restricted_operations = [
        operation
        for operation in ALL_OPERATIONS
        if operation != "detect_seam_activation"
    ]

    with pytest.raises(
        ConstitutionalViolationError,
        match="Unauthorized operation",
    ):
        TransitionOrchestrator().execute(
            contract=make_contract(
                allowed_operations=restricted_operations
            ),
            payload=make_payload(),
        )


def test_orchestrator_consumes_compiler_issued_seam_parameters():
    seam_active_result, _ = TransitionOrchestrator().execute(
        contract=make_contract(
            maximum_score_gap=0.50
        ),
        payload=make_payload(),
    )

    oriented_result, _ = TransitionOrchestrator().execute(
        contract=make_contract(
            maximum_score_gap=0.10
        ),
        payload=make_payload(),
    )

    assert seam_active_result.resolution_state == "SEAM_ACTIVE"
    assert oriented_result.resolution_state == "ORIENTED"


def test_orchestrator_execution_is_reproducible():
    runtime = TransitionOrchestrator()
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


def test_orchestrator_rejects_missing_seam_parameters():
    contract = make_contract()

    contract_without_parameters = TransitionContract(
        contract_id=contract.contract_id,
        transition_id=contract.transition_id,
        authority=contract.authority,
        constitution_version=contract.constitution_version,
        contract_version=contract.contract_version,
        allowed_operations=contract.allowed_operations,
        permitted_exports=contract.permitted_exports,
        prohibited_exports=contract.prohibited_exports,
        operation_parameters={},
    )

    with pytest.raises(
        ConstitutionalViolationError,
        match="Missing operation parameters",
    ):
        TransitionOrchestrator().execute(
            contract=contract_without_parameters,
            payload=make_payload(),
        )
