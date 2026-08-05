from dataclasses import dataclass
from typing import Literal, Tuple

from contracts.transition_contract import TransitionContract
from runtime.candidate_basin_evaluation import CandidateBasinEvaluation
from runtime.executor import ConstitutionalViolationError
from runtime.recognition_unit import RecognitionUnit
from runtime.serializer import canonical_hash


SeamActivationState = Literal[
    "UNACTIVATED",
    "ACTIVATED",
]


@dataclass(frozen=True)
class SeamDetectionParameters:
    """
    Compiler-issued parameters governing seam detection.

    The detector may consume these values.
    It may not invent or modify them.
    """

    maximum_score_gap: float
    minimum_top_score: float
    required_participant_count: int


@dataclass(frozen=True)
class SeamParticipant:
    """
    One evaluated basin participating in boundary-tension analysis.
    """

    basin_id: str
    evidence_score: float


@dataclass(frozen=True)
class SeamActivationCondition:
    """
    Immutable output of deterministic seam detection.

    This object records whether the evaluated basin relationship
    satisfies the compiler-issued activation conditions.

    It does not resolve final orientation.
    """

    condition_id: str
    recognition_unit_id: str
    evaluation_id: str
    participating_basins: Tuple[SeamParticipant, ...]
    leading_score: float
    secondary_score: float
    score_gap: float
    authorized_maximum_gap: float
    activation_state: SeamActivationState


def detect_seam_activation(
    evaluation: CandidateBasinEvaluation,
    recognition_unit: RecognitionUnit,
    contract: TransitionContract,
    parameters: SeamDetectionParameters,
) -> SeamActivationCondition:
    """
    Detect deterministic boundary tension between the two leading basins.

    Jurisdiction:
    - inspect an existing CandidateBasinEvaluation;
    - calculate the leading score gap;
    - compare that gap with compiler-issued parameters;
    - emit seam activation state.

    Prohibited:
    - generating candidate basins;
    - modifying evidence scores;
    - selecting the primary basin;
    - resolving final orientation.
    """
    if (
        evaluation.recognition_unit_id
        != recognition_unit.recognition_unit_id
    ):
        raise ConstitutionalViolationError(
            "Candidate evaluation and Recognition Unit identities do not match."
        )

    if "detect_seam_activation" not in contract.allowed_operations:
        raise ConstitutionalViolationError(
            "Unauthorized operation: 'detect_seam_activation' "
            f"is not permitted by contract '{contract.contract_id}'."
        )

    if parameters.required_participant_count != 2:
        raise ConstitutionalViolationError(
            "VS003 seam detection requires exactly two participants."
        )

    if parameters.maximum_score_gap < 0:
        raise ConstitutionalViolationError(
            "Maximum score gap cannot be negative."
        )

    if not 0 <= parameters.minimum_top_score <= 1:
        raise ConstitutionalViolationError(
            "Minimum top score must be between 0 and 1."
        )

    if len(evaluation.candidates) < 2:
        raise ConstitutionalViolationError(
            "Seam detection requires at least two evaluated candidates."
        )

    ordered_candidates = tuple(
        sorted(
            evaluation.candidates,
            key=lambda candidate: (
                -candidate.evidence_score,
                candidate.basin_id,
            ),
        )
    )

    top = ordered_candidates[0]
    secondary = ordered_candidates[1]

    if top.basin_id == secondary.basin_id:
        raise ConstitutionalViolationError(
            "Seam participants must have distinct basin identities."
        )

    score_gap = top.evidence_score - secondary.evidence_score

    activated = (
        top.evidence_score >= parameters.minimum_top_score
        and score_gap <= parameters.maximum_score_gap
    )

    participants = (
        SeamParticipant(
            basin_id=top.basin_id,
            evidence_score=top.evidence_score,
        ),
        SeamParticipant(
            basin_id=secondary.basin_id,
            evidence_score=secondary.evidence_score,
        ),
    )

    condition_material = {
        "recognition_unit_id": (
            recognition_unit.recognition_unit_id
        ),
        "evaluation_id": evaluation.evaluation_id,
        "participating_basins": [
            {
                "basin_id": participant.basin_id,
                "evidence_score": participant.evidence_score,
            }
            for participant in participants
        ],
        "leading_score": top.evidence_score,
        "secondary_score": secondary.evidence_score,
        "score_gap": score_gap,
        "authorized_maximum_gap": (
            parameters.maximum_score_gap
        ),
        "minimum_top_score": parameters.minimum_top_score,
        "required_participant_count": (
            parameters.required_participant_count
        ),
        "activation_state": (
            "ACTIVATED" if activated else "UNACTIVATED"
        ),
    }

    return SeamActivationCondition(
        condition_id=(
            "SAC-"
            + canonical_hash(condition_material)[:16].upper()
        ),
        recognition_unit_id=(
            recognition_unit.recognition_unit_id
        ),
        evaluation_id=evaluation.evaluation_id,
        participating_basins=participants,
        leading_score=top.evidence_score,
        secondary_score=secondary.evidence_score,
        score_gap=score_gap,
        authorized_maximum_gap=(
            parameters.maximum_score_gap
        ),
        activation_state=(
            "ACTIVATED" if activated else "UNACTIVATED"
        ),
    )
