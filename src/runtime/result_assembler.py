from dataclasses import dataclass

from contracts.transition_contract import TransitionContract
from runtime.basin_selector import BasinSelection
from runtime.candidate_basin_evaluation import CandidateBasinEvaluation
from runtime.executor import ConstitutionalViolationError
from runtime.ingress_payload import GovernedIngressPayload
from runtime.recognition_result import (
    BasinOrientation,
    Provenance,
    RecognitionResult,
)
from runtime.recognition_unit import RecognitionUnit
from runtime.serializer import canonical_hash


@dataclass(frozen=True)
class ResultAssemblyInputs:
    """
    Inputs admitted to RecognitionResult assembly.

    Every upstream decision is already complete.
    The assembler may bind and validate them, but cannot reinterpret them.
    """

    transition_id: str
    contract: TransitionContract
    payload: GovernedIngressPayload
    recognition_unit: RecognitionUnit
    evaluation: CandidateBasinEvaluation
    selection: BasinSelection


def assemble_recognition_result(
    inputs: ResultAssemblyInputs,
) -> RecognitionResult:
    """
    Assemble the final recognition result from governed upstream artifacts.

    Jurisdiction:
    - validate lineage continuity;
    - bind the completed selection into the output;
    - derive deterministic result identity.

    Prohibited:
    - generating candidates;
    - assigning evidence scores;
    - changing the selected basin;
    - executing remedy or protocol logic.
    """
    if (
        inputs.recognition_unit.ingress_payload_id
        != inputs.payload.payload_id
    ):
        raise ConstitutionalViolationError(
            "Recognition Unit and ingress payload identities do not match."
        )

    if (
        inputs.recognition_unit.ingress_payload_digest
        != inputs.payload.digest()
    ):
        raise ConstitutionalViolationError(
            "Recognition Unit does not preserve the supplied payload digest."
        )

    if (
        inputs.evaluation.recognition_unit_id
        != inputs.recognition_unit.recognition_unit_id
    ):
        raise ConstitutionalViolationError(
            "Candidate evaluation and Recognition Unit identities do not match."
        )

    if (
        inputs.selection.evaluation_id
        != inputs.evaluation.evaluation_id
    ):
        raise ConstitutionalViolationError(
            "Basin selection and candidate evaluation identities do not match."
        )

    evaluated_basin_ids = {
        candidate.basin_id
        for candidate in inputs.evaluation.candidates
    }

    if inputs.selection.primary_basin not in evaluated_basin_ids:
        raise ConstitutionalViolationError(
            "Selected basin is absent from the evaluated candidate set."
        )

    orientation = BasinOrientation(
        primary_basin=inputs.selection.primary_basin,
        active_seam=None,
        directional_momentum=None,
    )

    recognition_material = {
        "transition_id": inputs.transition_id,
        "contract_digest": inputs.contract.digest(),
        "payload_digest": inputs.payload.digest(),
        "recognition_unit_id": (
            inputs.recognition_unit.recognition_unit_id
        ),
        "evaluation_id": inputs.evaluation.evaluation_id,
        "selection_id": inputs.selection.selection_id,
        "primary_basin": inputs.selection.primary_basin,
        "resolution_state": "oriented",
    }

    recognition_id = (
        "RR-"
        + canonical_hash(recognition_material)[:16].upper()
    )

    return RecognitionResult(
        recognition_id=recognition_id,
        recognition_unit_id=(
            inputs.recognition_unit.recognition_unit_id
        ),
        orientation=orientation,
        resolution_state="oriented",
        residual_observations=[],
        provenance=Provenance(
            ingress_payload_id=inputs.payload.payload_id,
            contract_version=inputs.contract.contract_version,
        ),
    )