from dataclasses import replace

import pytest

from contracts.transition_contract import (
    AuthorityMetadata,
    TransitionContract,
)
from runtime.basin_selector import select_primary_basin
from runtime.candidate_evaluator import evaluate_candidate_basins
from runtime.candidate_generation import generate_candidate_basins
from runtime.ingress_payload import GovernedIngressPayload
from runtime.recognition_unit import instantiate_recognition_unit
from runtime.result_assembler import (
    ResultAssemblyInputs,
    assemble_recognition_result,
)
from runtime.transition import derive_transition_id
from runtime.vs002_telemetry import (
    VS002TelemetryInputs,
    emit_vs002_telemetry,
)


def make_inputs() -> VS002TelemetryInputs:
    contract = TransitionContract(
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
        allowed_operations=[
            "ingress_hash",
            "instantiate_recognition_unit",
            "generate_candidate_basins",
            "evaluate_candidate_basins",
            "determine_primary_basin",
            "record_rejected_basins",
            "assemble_recognition_result",
            "emit_transition_telemetry",
        ],
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
    )

    payload = GovernedIngressPayload(
        payload_id="ING-002",
        raw_observation="My system won't shut off.",
        source_type="user_report",
    )

    unit = instantiate_recognition_unit(payload)
    generation = generate_candidate_basins(unit)
    evaluation = evaluate_candidate_basins(generation, unit)
    selection = select_primary_basin(evaluation)
    transition_id = derive_transition_id(contract, payload)

    result = assemble_recognition_result(
        ResultAssemblyInputs(
            transition_id=transition_id,
            contract=contract,
            payload=payload,
            recognition_unit=unit,
            evaluation=evaluation,
            selection=selection,
        )
    )

    return VS002TelemetryInputs(
        transition_id=transition_id,
        contract=contract,
        payload_digest=payload.digest(),
        recognition_unit=unit,
        generation=generation,
        evaluation=evaluation,
        selection=selection,
        result=result,
        runtime_version="reos-runtime-0.2.0",
    )


def test_vs002_telemetry_records_complete_operation_chain():
    telemetry = emit_vs002_telemetry(make_inputs())

    assert [
        entry.operation_name
        for entry in telemetry.operation_trace
    ] == [
        "ingress_hash",
        "instantiate_recognition_unit",
        "generate_candidate_basins",
        "evaluate_candidate_basins",
        "determine_primary_basin",
        "record_rejected_basins",
        "assemble_recognition_result",
        "emit_transition_telemetry",
    ]


def test_vs002_telemetry_preserves_candidate_and_rejection_evidence():
    telemetry = emit_vs002_telemetry(make_inputs())

    assert telemetry.candidate_basins == [
        "REC-002",
        "REC-007",
    ]
    assert telemetry.selected_basin == "REC-002"
    assert len(telemetry.rejected_basins) == 1
    assert telemetry.rejected_basins[0].basin_id == "REC-007"


def test_vs002_telemetry_identity_is_reproducible():
    first = emit_vs002_telemetry(make_inputs())
    second = emit_vs002_telemetry(make_inputs())

    assert first == second


def test_vs002_telemetry_rejects_result_selection_disagreement():
    inputs = make_inputs()

    mismatched_result = replace(
        inputs.result,
        orientation=replace(
            inputs.result.orientation,
            primary_basin="REC-007",
        ),
    )

    with pytest.raises(
        ValueError,
        match="do not agree",
    ):
        emit_vs002_telemetry(
            replace(
                inputs,
                result=mismatched_result,
            )
        )