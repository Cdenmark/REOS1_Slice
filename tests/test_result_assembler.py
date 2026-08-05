from dataclasses import replace

import pytest

from contracts.transition_contract import (
    AuthorityMetadata,
    TransitionContract,
)
from runtime.basin_selector import select_primary_basin
from runtime.candidate_evaluator import evaluate_candidate_basins
from runtime.candidate_generation import generate_candidate_basins
from runtime.executor import ConstitutionalViolationError
from runtime.ingress_payload import GovernedIngressPayload
from runtime.recognition_unit import instantiate_recognition_unit
from runtime.result_assembler import (
    ResultAssemblyInputs,
    assemble_recognition_result,
)
from runtime.transition import derive_transition_id


def make_contract() -> TransitionContract:
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
        allowed_operations=[
            "ingress_hash",
            "instantiate_recognition_unit",
            "generate_candidate_basins",
            "evaluate_candidate_basins",
            "determine_primary_basin",
            "record_rejected_basins",
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
        operation_parameters={},
    )


def make_assembly_inputs() -> ResultAssemblyInputs:
    contract = make_contract()

    payload = GovernedIngressPayload(
        payload_id="ING-002",
        raw_observation="My system won't shut off.",
        source_type="user_report",
    )

    unit = instantiate_recognition_unit(payload)
    generation = generate_candidate_basins(unit)

    evaluation = evaluate_candidate_basins(
        generation=generation,
        recognition_unit=unit,
    )

    selection = select_primary_basin(evaluation)

    transition_id = derive_transition_id(
        contract=contract,
        payload=payload,
    )

    return ResultAssemblyInputs(
        transition_id=transition_id,
        contract=contract,
        payload=payload,
        recognition_unit=unit,
        evaluation=evaluation,
        selection=selection,
    )


def test_result_assembler_emits_selected_basin():
    inputs = make_assembly_inputs()

    result = assemble_recognition_result(inputs)

    assert result.orientation.primary_basin == "REC-002"
    assert result.resolution_state == "oriented"
    assert (
        result.recognition_unit_id
        == inputs.recognition_unit.recognition_unit_id
    )


def test_result_assembly_is_reproducible():
    inputs = make_assembly_inputs()

    first = assemble_recognition_result(inputs)
    second = assemble_recognition_result(inputs)

    assert first == second
    assert first.recognition_id == second.recognition_id


def test_result_assembler_rejects_evaluation_lineage_mismatch():
    inputs = make_assembly_inputs()

    mismatched_evaluation = replace(
        inputs.evaluation,
        recognition_unit_id="RU-DIFFERENT",
    )

    with pytest.raises(
        ConstitutionalViolationError,
        match="evaluation and Recognition Unit identities",
    ):
        assemble_recognition_result(
            replace(
                inputs,
                evaluation=mismatched_evaluation,
            )
        )


def test_result_assembler_rejects_selection_lineage_mismatch():
    inputs = make_assembly_inputs()

    mismatched_selection = replace(
        inputs.selection,
        evaluation_id="CBE-DIFFERENT",
    )

    with pytest.raises(
        ConstitutionalViolationError,
        match="selection and candidate evaluation identities",
    ):
        assemble_recognition_result(
            replace(
                inputs,
                selection=mismatched_selection,
            )
        )