from dataclasses import dataclass
from typing import Dict, Tuple

from runtime.candidate_basin_evaluation import (
    CandidateBasin,
    CandidateBasinEvaluation,
)
from runtime.candidate_generation import CandidateGenerationResult
from runtime.executor import ConstitutionalViolationError
from runtime.recognition_unit import RecognitionUnit
from runtime.serializer import canonical_hash


@dataclass(frozen=True)
class BasinEvaluationRule:
    """
    One deterministic assessment rule owned by the evaluator.

    The rule may score an already-generated candidate.
    It cannot generate a new candidate or select a winner.
    """

    basin_id: str
    required_evidence: Tuple[str, ...]
    score: float


VS002_EVALUATION_RULES: Dict[str, BasinEvaluationRule] = {
    "REC-002": BasinEvaluationRule(
        basin_id="REC-002",
        required_evidence=(
            "phrase:shut off",
            "mechanic:governor_failure",
        ),
        score=1.0,
    ),
    "REC-007": BasinEvaluationRule(
        basin_id="REC-007",
        required_evidence=(
            "phrase:system",
            "mechanic:processing_reference",
        ),
        score=0.50,
    ),
}


def evaluate_candidate_basins(
    generation: CandidateGenerationResult,
    recognition_unit: RecognitionUnit,
) -> CandidateBasinEvaluation:
    """
    Assign deterministic evidence scores to generated candidates.

    Jurisdiction:
    - consumes candidate presence;
    - evaluates only those candidates;
    - emits evidence scores and evidence basis.

    Prohibited:
    - generating new basins;
    - removing generated basins;
    - selecting the primary basin.
    """
    if (
        generation.recognition_unit_id
        != recognition_unit.recognition_unit_id
    ):
        raise ConstitutionalViolationError(
            "Candidate generation and Recognition Unit identities do not match."
        )

    evaluated_candidates = []

    for generated_candidate in generation.candidates:
        rule = VS002_EVALUATION_RULES.get(
            generated_candidate.basin_id
        )

        if rule is None:
            raise ConstitutionalViolationError(
                "No evaluator rule exists for generated basin "
                f"'{generated_candidate.basin_id}'."
            )

        eligibility_evidence = set(
            generated_candidate.eligibility_basis
        )

        required_evidence = set(rule.required_evidence)

        evidence_satisfied = (
            required_evidence.issubset(eligibility_evidence)
        )

        score = rule.score if evidence_satisfied else 0.0

        evaluated_candidates.append(
            CandidateBasin(
                basin_id=generated_candidate.basin_id,
                evidence_score=score,
                evidence_basis=(
                    generated_candidate.eligibility_basis
                    if evidence_satisfied
                    else (
                        *generated_candidate.eligibility_basis,
                        "evaluation:required_evidence_missing",
                    )
                ),
            )
        )

    ordered_candidates = tuple(
        sorted(
            evaluated_candidates,
            key=lambda candidate: candidate.basin_id,
        )
    )

    evaluation_material = {
        "generation_id": generation.generation_id,
        "recognition_unit_id": (
            recognition_unit.recognition_unit_id
        ),
        "candidates": [
            {
                "basin_id": candidate.basin_id,
                "evidence_score": candidate.evidence_score,
                "evidence_basis": list(
                    candidate.evidence_basis
                ),
            }
            for candidate in ordered_candidates
        ],
    }

    return CandidateBasinEvaluation(
        evaluation_id=(
            "CBE-"
            + canonical_hash(evaluation_material)[:16].upper()
        ),
        recognition_unit_id=(
            recognition_unit.recognition_unit_id
        ),
        candidates=ordered_candidates,
        deterministic=True,
    )