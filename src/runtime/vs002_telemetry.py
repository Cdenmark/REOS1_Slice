from dataclasses import dataclass
from typing import Tuple

from contracts.transition_contract import TransitionContract
from runtime.basin_selector import BasinSelection
from runtime.candidate_basin_evaluation import CandidateBasinEvaluation
from runtime.candidate_generation import CandidateGenerationResult
from runtime.recognition_result import RecognitionResult
from runtime.recognition_unit import RecognitionUnit
from runtime.transition_telemetry import (
    ArtifactLineage,
    OperationTraceEntry,
    RejectedBasin,
    TransitionTelemetry,
)


@dataclass(frozen=True)
class VS002TelemetryInputs:
    """
    Completed artifacts admitted to VS002 telemetry emission.

    The emitter records execution that has already occurred.
    It cannot create or reinterpret upstream artifacts.
    """

    transition_id: str
    contract: TransitionContract
    payload_digest: str
    recognition_unit: RecognitionUnit
    generation: CandidateGenerationResult
    evaluation: CandidateBasinEvaluation
    selection: BasinSelection
    result: RecognitionResult
    runtime_version: str


def emit_vs002_telemetry(
    inputs: VS002TelemetryInputs,
) -> TransitionTelemetry:
    """
    Emit immutable VS002 transition telemetry.

    Jurisdiction:
    - record the ordered operation chain;
    - preserve candidate and rejection evidence;
    - bind execution lineage.

    Prohibited:
    - generating candidates;
    - assigning scores;
    - selecting a basin;
    - changing the RecognitionResult.
    """
    if (
        inputs.generation.recognition_unit_id
        != inputs.recognition_unit.recognition_unit_id
    ):
        raise ValueError(
            "Generation and Recognition Unit identities do not match."
        )

    if (
        inputs.evaluation.recognition_unit_id
        != inputs.recognition_unit.recognition_unit_id
    ):
        raise ValueError(
            "Evaluation and Recognition Unit identities do not match."
        )

    if (
        inputs.selection.evaluation_id
        != inputs.evaluation.evaluation_id
    ):
        raise ValueError(
            "Selection and evaluation identities do not match."
        )

    if (
        inputs.result.recognition_unit_id
        != inputs.recognition_unit.recognition_unit_id
    ):
        raise ValueError(
            "Recognition Result and Recognition Unit identities do not match."
        )

    if (
        inputs.result.orientation.primary_basin
        != inputs.selection.primary_basin
    ):
        raise ValueError(
            "Recognition Result and Basin Selection do not agree."
        )

    rejected_basins = tuple(
        RejectedBasin(
            basin_id=rejection.basin_id,
            rejection_reason=rejection.rejection_reason,
        )
        for rejection in inputs.selection.rejected_basins
    )

    return TransitionTelemetry(
        trace_id=f"TRACE-{inputs.transition_id}",
        transition_id=inputs.transition_id,
        declaration_hash=inputs.contract.authority.declaration_hash,
        constitution_version=inputs.contract.constitution_version,
        compiler_version=inputs.contract.authority.compiler_release,
        contract_version=inputs.contract.contract_version,
        runtime_version=inputs.runtime_version,
        operation_trace=[
            OperationTraceEntry(
                sequence=1,
                operation_name="ingress_hash",
            ),
            OperationTraceEntry(
                sequence=2,
                operation_name="instantiate_recognition_unit",
            ),
            OperationTraceEntry(
                sequence=3,
                operation_name="generate_candidate_basins",
            ),
            OperationTraceEntry(
                sequence=4,
                operation_name="evaluate_candidate_basins",
            ),
            OperationTraceEntry(
                sequence=5,
                operation_name="determine_primary_basin",
            ),
            OperationTraceEntry(
                sequence=6,
                operation_name="record_rejected_basins",
            ),
            OperationTraceEntry(
                sequence=7,
                operation_name="assemble_recognition_result",
            ),
            OperationTraceEntry(
                sequence=8,
                operation_name="emit_transition_telemetry",
            ),
        ],
        candidate_basins=[
            candidate.basin_id
            for candidate in inputs.evaluation.candidates
        ],
        selected_basin=inputs.selection.primary_basin,
        rejected_basins=list(rejected_basins),
        evaluated_seams=[],
        termination_reason="MULTI_BASIN_ORIENTATION_SUCCESS",
        lineage=ArtifactLineage(
            parent_artifacts=[
                inputs.payload_digest,
                inputs.contract.digest(),
                inputs.recognition_unit.digest(),
                inputs.generation.generation_id,
                inputs.evaluation.evaluation_id,
                inputs.selection.selection_id,
                inputs.result.recognition_id,
            ],
            produced_by=f"runtime:{inputs.runtime_version}",
            certified_by=(
                f"compiler:{inputs.contract.authority.compiler_release}"
            ),
        ),
    )