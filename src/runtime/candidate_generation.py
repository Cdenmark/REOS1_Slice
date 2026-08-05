from dataclasses import dataclass
from typing import Tuple

from runtime.executor import ConstitutionalViolationError
from runtime.recognition_unit import RecognitionUnit
from runtime.serializer import canonical_hash


@dataclass(frozen=True)
class GeneratedBasinCandidate:
    """
    One basin found to be topologically eligible.

    This object records eligibility only.
    It owns no evidence score and no selection status.
    """

    basin_id: str
    eligibility_basis: Tuple[str, ...]


@dataclass(frozen=True)
class CandidateGenerationResult:
    """
    Immutable output of candidate discovery.

    The generator owns candidate presence.
    It does not evaluate, rank, reject, or select candidates.
    """

    generation_id: str
    recognition_unit_id: str
    candidates: Tuple[GeneratedBasinCandidate, ...]


def generate_candidate_basins(
    recognition_unit: RecognitionUnit,
) -> CandidateGenerationResult:
    """
    Deterministic VS002 candidate discovery.

    This narrow proof recognizes eligibility signals for:
    - REC-002: autonomic governor failure
    - REC-007: neuro-cognitive processing disruption

    At least two eligible basins are required for VS002.
    """
    observation = recognition_unit.literal_observation.casefold()

    candidates: list[GeneratedBasinCandidate] = []

    if "shut off" in observation:
        candidates.append(
            GeneratedBasinCandidate(
                basin_id="REC-002",
                eligibility_basis=(
                    "phrase:shut off",
                    "mechanic:governor_failure",
                ),
            )
        )

    if "system" in observation:
        candidates.append(
            GeneratedBasinCandidate(
                basin_id="REC-007",
                eligibility_basis=(
                    "phrase:system",
                    "mechanic:processing_reference",
                ),
            )
        )

    if len(candidates) < 2:
        raise ConstitutionalViolationError(
            "VS002 candidate generation requires at least two eligible basins."
        )

    ordered_candidates = tuple(
        sorted(candidates, key=lambda candidate: candidate.basin_id)
    )

    generation_material = {
        "recognition_unit_id": recognition_unit.recognition_unit_id,
        "candidates": [
            {
                "basin_id": candidate.basin_id,
                "eligibility_basis": list(candidate.eligibility_basis),
            }
            for candidate in ordered_candidates
        ],
    }

    return CandidateGenerationResult(
        generation_id=(
            "CBG-"
            + canonical_hash(generation_material)[:16].upper()
        ),
        recognition_unit_id=recognition_unit.recognition_unit_id,
        candidates=ordered_candidates,
    )