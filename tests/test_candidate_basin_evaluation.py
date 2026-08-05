from runtime.candidate_basin_evaluation import (
    CandidateBasin,
    CandidateBasinEvaluation,
)


def test_candidate_basin_evaluation_preserves_candidates():
    evaluation = CandidateBasinEvaluation(
        evaluation_id="CBE-001",
        recognition_unit_id="RU-001",
        candidates=(
            CandidateBasin(
                basin_id="REC-002",
                evidence_score=0.92,
                evidence_basis=(
                    "phrase:shut off",
                    "mechanic:governor_failure",
                ),
            ),
            CandidateBasin(
                basin_id="REC-007",
                evidence_score=0.54,
                evidence_basis=(
                    "phrase:system",
                ),
            ),
        ),
    )

    assert len(evaluation.candidates) == 2
    assert evaluation.candidates[0].basin_id == "REC-002"
    assert evaluation.candidates[0].evidence_score == 0.92
    assert evaluation.deterministic is True


def test_evaluation_contains_no_selection_authority():
    candidate = CandidateBasin(
        basin_id="REC-002",
        evidence_score=0.92,
    )

    assert not hasattr(candidate, "selected")
    assert not hasattr(candidate, "rejection_reason")