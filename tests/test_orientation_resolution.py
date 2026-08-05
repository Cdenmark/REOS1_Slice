from dataclasses import replace

import pytest

from runtime.basin_selector import (
    BasinRejection,
    BasinSelection,
)
from runtime.executor import ConstitutionalViolationError
from runtime.orientation_resolution import resolve_orientation
from runtime.seam_activation import (
    SeamActivationCondition,
    SeamParticipant,
)


def make_selection() -> BasinSelection:
    return BasinSelection(
        selection_id="BSEL-003",
        evaluation_id="CBE-003",
        primary_basin="REC-002",
        primary_score=0.82,
        rejected_basins=(
            BasinRejection(
                basin_id="REC-007",
                evidence_score=0.76,
                rejection_reason="LOWER_EVIDENCE_SCORE",
            ),
        ),
    )


def make_seam_condition(
    *,
    activation_state: str,
) -> SeamActivationCondition:
    return SeamActivationCondition(
        condition_id="SAC-003",
        recognition_unit_id="RU-003",
        evaluation_id="CBE-003",
        participating_basins=(
            SeamParticipant(
                basin_id="REC-002",
                evidence_score=0.82,
            ),
            SeamParticipant(
                basin_id="REC-007",
                evidence_score=0.76,
            ),
        ),
        leading_score=0.82,
        secondary_score=0.76,
        score_gap=0.06,
        authorized_maximum_gap=0.10,
        activation_state=activation_state,
    )


def test_resolver_emits_seam_active_orientation():
    resolution = resolve_orientation(
        selection=make_selection(),
        seam_condition=make_seam_condition(
            activation_state="ACTIVATED"
        ),
    )

    assert resolution.primary_basin == "REC-002"
    assert resolution.resolution_state == "SEAM_ACTIVE"
    assert resolution.active_seam is not None
    assert resolution.active_seam.participating_basins == (
        "REC-002",
        "REC-007",
    )


def test_resolver_preserves_oriented_state_when_seam_is_inactive():
    resolution = resolve_orientation(
        selection=make_selection(),
        seam_condition=make_seam_condition(
            activation_state="UNACTIVATED"
        ),
    )

    assert resolution.primary_basin == "REC-002"
    assert resolution.resolution_state == "ORIENTED"
    assert resolution.active_seam is None


def test_orientation_resolution_is_reproducible():
    selection = make_selection()
    seam_condition = make_seam_condition(
        activation_state="ACTIVATED"
    )

    first = resolve_orientation(
        selection=selection,
        seam_condition=seam_condition,
    )

    second = resolve_orientation(
        selection=selection,
        seam_condition=seam_condition,
    )

    assert first == second
    assert first.resolution_id == second.resolution_id


def test_resolver_rejects_evaluation_lineage_mismatch():
    seam_condition = replace(
        make_seam_condition(activation_state="ACTIVATED"),
        evaluation_id="CBE-DIFFERENT",
    )

    with pytest.raises(
        ConstitutionalViolationError,
        match="evaluation identities do not match",
    ):
        resolve_orientation(
            selection=make_selection(),
            seam_condition=seam_condition,
        )


def test_resolver_rejects_primary_basin_absent_from_seam():
    seam_condition = replace(
        make_seam_condition(activation_state="ACTIVATED"),
        participating_basins=(
            SeamParticipant(
                basin_id="REC-007",
                evidence_score=0.76,
            ),
            SeamParticipant(
                basin_id="REC-010",
                evidence_score=0.74,
            ),
        ),
    )

    with pytest.raises(
        ConstitutionalViolationError,
        match="absent from the seam participants",
    ):
        resolve_orientation(
            selection=make_selection(),
            seam_condition=seam_condition,
        )


def test_resolver_does_not_change_selected_primary_basin():
    selection = make_selection()

    resolution = resolve_orientation(
        selection=selection,
        seam_condition=make_seam_condition(
            activation_state="ACTIVATED"
        ),
    )

    assert resolution.primary_basin == selection.primary_basin
    assert selection.primary_basin == "REC-002"
