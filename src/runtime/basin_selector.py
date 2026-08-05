from dataclasses import dataclass
from typing import Literal, Tuple

from runtime.candidate_basin_evaluation import (
    CandidateBasinEvaluation,
)
from runtime.executor import ConstitutionalViolationError
from runtime.serializer import canonical_hash


SelectionState = Literal["ORIENTED"]


@dataclass(frozen=True)
class BasinRejection:
    """One candidate rejected by deterministic basin selection."""

    basin_id: str
    evidence_score: float
    rejection_reason: str


@dataclass(frozen=True)
class BasinSelection:
    """
    Immutable output of the VS002 basin selector.

    This object owns the selection decision.
    It does not own candidate generation or final RecognitionResult emission.
    """

    selection_id: str
    evaluation_id: str
    primary_basin: str
    primary_score: float
    rejected_basins: Tuple[BasinRejection, ...]
    resolution_state: SelectionState = "ORIENTED"


def select_primary_basin(
    evaluation: CandidateBasinEvaluation,
) -> BasinSelection:
    """
    Select exactly one highest-scoring basin or fail closed.

    VS002 requires:
    - at least two candidates;
    - unique basin identities;
    - one strictly highest score;
    - no tie-breaking fallback.
    """
    candidates = evaluation.candidates

    if len(candidates) < 2:
        raise ConstitutionalViolationError(
            "Multi-basin selection requires at least two candidates."
        )

    basin_ids = [candidate.basin_id for candidate in candidates]

    if len(set(basin_ids)) != len(basin_ids):
        raise ConstitutionalViolationError(
            "Candidate evaluation contains duplicate basin identities."
        )

    highest_score = max(
        candidate.evidence_score
        for candidate in candidates
    )

    leaders = tuple(
        candidate
        for candidate in candidates
        if candidate.evidence_score == highest_score
    )

    if len(leaders) != 1:
        raise ConstitutionalViolationError(
            "Candidate basin evaluation produced an unresolved tie."
        )

    selected = leaders[0]

    rejected = tuple(
        BasinRejection(
            basin_id=candidate.basin_id,
            evidence_score=candidate.evidence_score,
            rejection_reason="LOWER_EVIDENCE_SCORE",
        )
        for candidate in sorted(
            candidates,
            key=lambda item: item.basin_id,
        )
        if candidate.basin_id != selected.basin_id
    )

    selection_material = {
        "evaluation_id": evaluation.evaluation_id,
        "recognition_unit_id": evaluation.recognition_unit_id,
        "primary_basin": selected.basin_id,
        "primary_score": selected.evidence_score,
        "rejected_basins": [
            {
                "basin_id": rejection.basin_id,
                "evidence_score": rejection.evidence_score,
                "rejection_reason": rejection.rejection_reason,
            }
            for rejection in rejected
        ],
    }

    return BasinSelection(
        selection_id=(
            "BSEL-"
            + canonical_hash(selection_material)[:16].upper()
        ),
        evaluation_id=evaluation.evaluation_id,
        primary_basin=selected.basin_id,
        primary_score=selected.evidence_score,
        rejected_basins=rejected,
    )