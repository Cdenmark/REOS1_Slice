import pytest

from runtime.basin_selector import select_primary_basin
from runtime.candidate_basin_evaluation import (
    CandidateBasin,
    CandidateBasinEvaluation,
)
from runtime.executor import ConstitutionalViolationError


def make_evaluation(
    candidates: tuple[CandidateBasin, ...],
) -> CandidateBasinEvaluation:
    return CandidateBasinEvaluation(
        evaluation_id="CBE-001",
        recognition_unit_id="RU-001",
        candidates=candidates,
    )


def test_selector_selects_single_highest_scoring_basin():
    selection = select_primary_basin(
        make_evaluation(
            (
                CandidateBasin("REC-002", 0.92),
                CandidateBasin("REC-007", 0.54),
                CandidateBasin("REC-010", 0.31),
            )
        )
    )

    assert selection.primary_basin == "REC-002"
    assert selection.primary_score == 0.92
    assert selection.resolution_state == "ORIENTED"


def test_selector_preserves_rejected_candidates():
    selection = select_primary_basin(
        make_evaluation(
            (
                CandidateBasin("REC-002", 0.92),
                CandidateBasin("REC-007", 0.54),
            )
        )
    )

    assert len(selection.rejected_basins) == 1
    assert selection.rejected_basins[0].basin_id == "REC-007"
    assert (
        selection.rejected_basins[0].rejection_reason
        == "LOWER_EVIDENCE_SCORE"
    )


def test_selector_identity_is_reproducible():
    evaluation = make_evaluation(
        (
            CandidateBasin("REC-002", 0.92),
            CandidateBasin("REC-007", 0.54),
        )
    )

    first = select_primary_basin(evaluation)
    second = select_primary_basin(evaluation)

    assert first == second
    assert first.selection_id == second.selection_id


def test_selector_fails_closed_on_tie():
    with pytest.raises(
        ConstitutionalViolationError,
        match="unresolved tie",
    ):
        select_primary_basin(
            make_evaluation(
                (
                    CandidateBasin("REC-002", 0.80),
                    CandidateBasin("REC-007", 0.80),
                )
            )
        )


def test_selector_fails_closed_with_only_one_candidate():
    with pytest.raises(
        ConstitutionalViolationError,
        match="at least two candidates",
    ):
        select_primary_basin(
            make_evaluation(
                (
                    CandidateBasin("REC-002", 0.92),
                )
            )
        )


def test_selector_rejects_duplicate_basin_identities():
    with pytest.raises(
        ConstitutionalViolationError,
        match="duplicate basin identities",
    ):
        select_primary_basin(
            make_evaluation(
                (
                    CandidateBasin("REC-002", 0.92),
                    CandidateBasin("REC-002", 0.54),
                )
            )
        )