from dataclasses import replace

import pytest

from contracts.transition_contract import (
    AuthorityMetadata,
    TransitionContract,
)
from runtime.basin_selector import select_primary_basin
from runtime.candidate_basin_evaluation import (
    CandidateBasin,
    CandidateBasinEvaluation,
)
from runtime.candidate_generation import (
    CandidateGenerationResult,
    GeneratedBasinCandidate,
)
from runtime.executor import ConstitutionalViolationError
from runtime.ingress_payload import GovernedIngressPayload
from runtime.orientation_resolution import resolve_orientation
from runtime.recognition_result import (
    BasinOrientation,
    Provenance,
    RecognitionResult,
)
from runtime.recognition_unit import instantiate_recognition_unit
from runtime.seam_activation import (
    SeamDetectionParameters,
    detect_seam_activation,
)
from runtime.seam_aware_recognition_result import (
    assemble_seam_aware_recognition_result,
)
from runtime.transition import derive_transition_id
from runtime.vs003_telemetry import (
    emit_vs003_transition_telemetry,
)


def make_contract() -> TransitionContract:
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
        allowed_operations=[
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
        ],
        permitted_exports=[
            "recognition_result",
            "seam_activation_condition",
            "orientation_resolution",
            "seam_aware_recognition_result",
            "transition_telemetry",
        ],
        prohibited_exports=[
            "execute_shunt",
            "remedy_selection",
            "protocol_generation",
        ],
        operation_parameters={},
    )


def make_artifacts():
    contract = make_contract()

    payload = GovernedIngressPayload(
        payload_id="ING-003",
        raw_observation="My system won't shut off.",
        source_type="user_report",
    )

    unit = instantiate_recognition_unit(payload)

    generation = CandidateGenerationResult(
        generation_id="CBG-003",
        recognition_unit_id=unit.recognition_unit_id,
        candidates=(
            GeneratedBasinCandidate(
                basin_id="REC-002",
                eligibility_basis=(
                    "phrase:shut off",
                    "mechanic:governor_failure",
                ),
            ),
            GeneratedBasinCandidate(
                basin_id="REC-007",
                eligibility_basis=(
                    "phrase:system",
                    "mechanic:processing_reference",
                ),
            ),
        ),
    )

    evaluation = CandidateBasinEvaluation(
        evaluation_id="CBE-003",
        recognition_unit_id=unit.recognition_unit_id,
        candidates=(
            CandidateBasin(
                basin_id="REC-002",
                evidence_score=0.82,
                evidence_basis=(
                    "phrase:shut off",
                    "mechanic:governor_failure",
                ),
            ),
            CandidateBasin(
                basin_id="REC-007",
                evidence_score=0.76,
                evidence_basis=(
                    "phrase:system",
                    "mechanic:processing_reference",
                ),
            ),
        ),
    )

    selection = select_primary_basin(evaluation)

    seam_condition = detect_seam_activation(
        evaluation=evaluation,
        recognition_unit=unit,
        contract=contract,
        parameters=SeamDetectionParameters(
            maximum_score_gap=0.10,
            minimum_top_score=0.50,
            required_participant_count=2,
        ),
    )

    resolution = resolve_orientation(
        selection=selection,
        seam_condition=seam_condition,
    )

    base_result = RecognitionResult(
        recognition_id="RR-003",
        recognition_unit_id=unit.recognition_unit_id,
        orientation=BasinOrientation(
            primary_basin=selection.primary_basin,
        ),
        resolution_state="oriented",
        residual_observations=[],
        provenance=Provenance(
            ingress_payload_id=payload.payload_id,
            contract_version=contract.contract_version,
        ),
    )

    result = assemble_seam_aware_recognition_result(
        base_result=base_result,
        orientation_resolution=resolution,
    )

    transition_id = derive_transition_id(
        contract=contract,
        payload=payload,
    )

    return (
        transition_id,
        unit,
        generation,
        evaluation,
        selection,
        seam_condition,
        resolution,
        result,
        contract,
    )


def test_vs003_telemetry_records_dag_lineage():
    (
        transition_id,
        unit,
        generation,
        evaluation,
        selection,
        seam_condition,
        resolution,
        result,
        contract,
    ) = make_artifacts()

    telemetry = emit_vs003_transition_telemetry(
        transition_id=transition_id,
        recognition_unit=unit,
        generation=generation,
        evaluation=evaluation,
        selection=selection,
        seam_condition=seam_condition,
        orientation_resolution=resolution,
        result=result,
        contract=contract,
    )

    assert telemetry.transition_id == transition_id
    assert telemetry.selection_id == selection.selection_id
    assert (
        telemetry.seam_condition_id
        == seam_condition.condition_id
    )
    assert (
        telemetry.orientation_resolution_id
        == resolution.resolution_id
    )
    assert telemetry.result_id == result.result_id


def test_vs003_telemetry_records_parallel_branches():
    artifacts = make_artifacts()

    telemetry = emit_vs003_transition_telemetry(
        transition_id=artifacts[0],
        recognition_unit=artifacts[1],
        generation=artifacts[2],
        evaluation=artifacts[3],
        selection=artifacts[4],
        seam_condition=artifacts[5],
        orientation_resolution=artifacts[6],
        result=artifacts[7],
        contract=artifacts[8],
    )

    branch_operations = {
        entry.branch: entry.operation_name
        for entry in telemetry.operation_trace
    }

    assert branch_operations["selection"] in {
        "determine_primary_basin",
        "record_rejected_basins",
    }
    assert (
        branch_operations["seam_detection"]
        == "detect_seam_activation"
    )
    assert branch_operations["convergence"] == "resolve_orientation"


def test_vs003_telemetry_is_reproducible():
    artifacts = make_artifacts()

    first = emit_vs003_transition_telemetry(
        transition_id=artifacts[0],
        recognition_unit=artifacts[1],
        generation=artifacts[2],
        evaluation=artifacts[3],
        selection=artifacts[4],
        seam_condition=artifacts[5],
        orientation_resolution=artifacts[6],
        result=artifacts[7],
        contract=artifacts[8],
    )

    second = emit_vs003_transition_telemetry(
        transition_id=artifacts[0],
        recognition_unit=artifacts[1],
        generation=artifacts[2],
        evaluation=artifacts[3],
        selection=artifacts[4],
        seam_condition=artifacts[5],
        orientation_resolution=artifacts[6],
        result=artifacts[7],
        contract=artifacts[8],
    )

    assert first == second
    assert first.telemetry_id == second.telemetry_id


def test_vs003_telemetry_rejects_seam_lineage_mismatch():
    artifacts = make_artifacts()

    mismatched_seam = replace(
        artifacts[5],
        evaluation_id="CBE-DIFFERENT",
    )

    with pytest.raises(
        ConstitutionalViolationError,
        match="Seam condition and candidate evaluation",
    ):
        emit_vs003_transition_telemetry(
            transition_id=artifacts[0],
            recognition_unit=artifacts[1],
            generation=artifacts[2],
            evaluation=artifacts[3],
            selection=artifacts[4],
            seam_condition=mismatched_seam,
            orientation_resolution=artifacts[6],
            result=artifacts[7],
            contract=artifacts[8],
        )


def test_vs003_telemetry_does_not_mutate_artifacts():
    artifacts = make_artifacts()

    original_evaluation = artifacts[3]
    original_selection = artifacts[4]
    original_seam = artifacts[5]

    emit_vs003_transition_telemetry(
        transition_id=artifacts[0],
        recognition_unit=artifacts[1],
        generation=artifacts[2],
        evaluation=artifacts[3],
        selection=artifacts[4],
        seam_condition=artifacts[5],
        orientation_resolution=artifacts[6],
        result=artifacts[7],
        contract=artifacts[8],
    )

    assert artifacts[3] == original_evaluation
    assert artifacts[4] == original_selection
    assert artifacts[5] == original_seam
