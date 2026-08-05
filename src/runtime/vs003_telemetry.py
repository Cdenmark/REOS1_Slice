from dataclasses import asdict, dataclass
from typing import Tuple

from contracts.transition_contract import TransitionContract
from runtime.basin_selector import BasinSelection
from runtime.candidate_basin_evaluation import CandidateBasinEvaluation
from runtime.candidate_generation import CandidateGenerationResult
from runtime.executor import ConstitutionalViolationError
from runtime.orientation_resolution import OrientationResolution
from runtime.recognition_unit import RecognitionUnit
from runtime.seam_activation import SeamActivationCondition
from runtime.seam_aware_recognition_result import (
    SeamAwareRecognitionResult,
)
from runtime.serializer import canonical_hash


@dataclass(frozen=True)
class VS003OperationTraceEntry:
    """
    One ordered operation witnessed by VS003 telemetry.

    This records execution only.
    It does not authorize or perform the operation.
    """

    sequence: int
    operation_name: str
    branch: str


@dataclass(frozen=True)
class VS003TransitionTelemetry:
    """
    Immutable evidence record for one VS003 transition.

    It witnesses:
    - the frozen VS002 decision branch;
    - the VS003 seam-detection branch;
    - their convergence in OrientationResolution;
    - the resulting seam-aware recognition artifact.

    It owns no scoring, selection, detection, or resolution authority.
    """

    telemetry_id: str
    transition_id: str

    recognition_unit_id: str
    generation_id: str
    evaluation_id: str
    selection_id: str
    seam_condition_id: str
    orientation_resolution_id: str
    result_id: str

    candidate_generation_digest: str
    candidate_evaluation_digest: str
    selection_digest: str
    seam_condition_digest: str
    orientation_resolution_digest: str
    result_digest: str

    operation_trace: Tuple[VS003OperationTraceEntry, ...]

    declaration_hash: str
    constitution_version: str
    compiler_version: str
    contract_version: str
    runtime_version: str

    termination_reason: str
    deterministic: bool = True


def emit_vs003_transition_telemetry(
    *,
    transition_id: str,
    recognition_unit: RecognitionUnit,
    generation: CandidateGenerationResult,
    evaluation: CandidateBasinEvaluation,
    selection: BasinSelection,
    seam_condition: SeamActivationCondition,
    orientation_resolution: OrientationResolution,
    result: SeamAwareRecognitionResult,
    contract: TransitionContract,
    runtime_version: str = "reos-runtime-0.3.0",
) -> VS003TransitionTelemetry:
    """
    Emit immutable evidence for the complete VS003 DAG.

    Jurisdiction:
    - verify lineage continuity;
    - record both independent branches;
    - bind artifact identities and deterministic digests;
    - preserve compiler and contract authority metadata.

    Prohibited:
    - generating or removing candidates;
    - assigning or modifying evidence scores;
    - selecting a basin;
    - calculating seam tension;
    - resolving orientation;
    - modifying any consumed artifact.
    """
    recognition_unit_id = recognition_unit.recognition_unit_id

    if generation.recognition_unit_id != recognition_unit_id:
        raise ConstitutionalViolationError(
            "Candidate generation and Recognition Unit identities do not match."
        )

    if evaluation.recognition_unit_id != recognition_unit_id:
        raise ConstitutionalViolationError(
            "Candidate evaluation and Recognition Unit identities do not match."
        )

    if seam_condition.recognition_unit_id != recognition_unit_id:
        raise ConstitutionalViolationError(
            "Seam condition and Recognition Unit identities do not match."
        )

    if result.base_result.recognition_unit_id != recognition_unit_id:
        raise ConstitutionalViolationError(
            "Seam-aware result and Recognition Unit identities do not match."
        )

    if selection.evaluation_id != evaluation.evaluation_id:
        raise ConstitutionalViolationError(
            "Basin selection and candidate evaluation identities do not match."
        )

    if seam_condition.evaluation_id != evaluation.evaluation_id:
        raise ConstitutionalViolationError(
            "Seam condition and candidate evaluation identities do not match."
        )

    if orientation_resolution.selection_id != selection.selection_id:
        raise ConstitutionalViolationError(
            "Orientation resolution and Basin Selection identities do not match."
        )

    if (
        orientation_resolution.seam_condition_id
        != seam_condition.condition_id
    ):
        raise ConstitutionalViolationError(
            "Orientation resolution and Seam Activation Condition "
            "identities do not match."
        )

    if (
        result.orientation_resolution_id
        != orientation_resolution.resolution_id
    ):
        raise ConstitutionalViolationError(
            "Seam-aware result and Orientation Resolution identities do not match."
        )

    if result.primary_basin != selection.primary_basin:
        raise ConstitutionalViolationError(
            "Seam-aware result and Basin Selection primary basins do not match."
        )

    if (
        orientation_resolution.primary_basin
        != selection.primary_basin
    ):
        raise ConstitutionalViolationError(
            "Orientation Resolution and Basin Selection primary basins do not match."
        )

    generation_digest = canonical_hash(asdict(generation))
    evaluation_digest = canonical_hash(asdict(evaluation))
    selection_digest = canonical_hash(asdict(selection))
    seam_condition_digest = canonical_hash(asdict(seam_condition))
    orientation_resolution_digest = canonical_hash(
        asdict(orientation_resolution)
    )
    result_digest = canonical_hash(asdict(result))

    operation_trace = (
        VS003OperationTraceEntry(
            sequence=1,
            operation_name="ingress_hash",
            branch="shared",
        ),
        VS003OperationTraceEntry(
            sequence=2,
            operation_name="instantiate_recognition_unit",
            branch="shared",
        ),
        VS003OperationTraceEntry(
            sequence=3,
            operation_name="generate_candidate_basins",
            branch="shared",
        ),
        VS003OperationTraceEntry(
            sequence=4,
            operation_name="evaluate_candidate_basins",
            branch="shared",
        ),
        VS003OperationTraceEntry(
            sequence=5,
            operation_name="determine_primary_basin",
            branch="selection",
        ),
        VS003OperationTraceEntry(
            sequence=6,
            operation_name="record_rejected_basins",
            branch="selection",
        ),
        VS003OperationTraceEntry(
            sequence=7,
            operation_name="detect_seam_activation",
            branch="seam_detection",
        ),
        VS003OperationTraceEntry(
            sequence=8,
            operation_name="resolve_orientation",
            branch="convergence",
        ),
        VS003OperationTraceEntry(
            sequence=9,
            operation_name="assemble_recognition_result",
            branch="assembly",
        ),
        VS003OperationTraceEntry(
            sequence=10,
            operation_name="emit_transition_telemetry",
            branch="telemetry",
        ),
    )

    telemetry_material = {
        "transition_id": transition_id,
        "recognition_unit_id": recognition_unit_id,
        "generation_id": generation.generation_id,
        "evaluation_id": evaluation.evaluation_id,
        "selection_id": selection.selection_id,
        "seam_condition_id": seam_condition.condition_id,
        "orientation_resolution_id": (
            orientation_resolution.resolution_id
        ),
        "result_id": result.result_id,
        "candidate_generation_digest": generation_digest,
        "candidate_evaluation_digest": evaluation_digest,
        "selection_digest": selection_digest,
        "seam_condition_digest": seam_condition_digest,
        "orientation_resolution_digest": (
            orientation_resolution_digest
        ),
        "result_digest": result_digest,
        "operation_trace": [
            asdict(entry)
            for entry in operation_trace
        ],
        "declaration_hash": contract.authority.declaration_hash,
        "constitution_version": contract.constitution_version,
        "compiler_version": contract.authority.compiler_release,
        "contract_version": contract.contract_version,
        "runtime_version": runtime_version,
        "termination_reason": (
            "SEAM_AWARE_ORIENTATION_COMPLETE"
        ),
    }

    return VS003TransitionTelemetry(
        telemetry_id=(
            "TEL3-"
            + canonical_hash(telemetry_material)[:16].upper()
        ),
        transition_id=transition_id,
        recognition_unit_id=recognition_unit_id,
        generation_id=generation.generation_id,
        evaluation_id=evaluation.evaluation_id,
        selection_id=selection.selection_id,
        seam_condition_id=seam_condition.condition_id,
        orientation_resolution_id=(
            orientation_resolution.resolution_id
        ),
        result_id=result.result_id,
        candidate_generation_digest=generation_digest,
        candidate_evaluation_digest=evaluation_digest,
        selection_digest=selection_digest,
        seam_condition_digest=seam_condition_digest,
        orientation_resolution_digest=(
            orientation_resolution_digest
        ),
        result_digest=result_digest,
        operation_trace=operation_trace,
        declaration_hash=contract.authority.declaration_hash,
        constitution_version=contract.constitution_version,
        compiler_version=contract.authority.compiler_release,
        contract_version=contract.contract_version,
        runtime_version=runtime_version,
        termination_reason="SEAM_AWARE_ORIENTATION_COMPLETE",
    )
