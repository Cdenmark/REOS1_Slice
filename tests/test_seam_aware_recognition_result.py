from dataclasses import replace

import pytest

from runtime.executor import ConstitutionalViolationError
from runtime.orientation_resolution import (
    ActiveSeam,
    OrientationResolution,
)
from runtime.recognition_result import (
    BasinOrientation,
    Provenance,
    RecognitionResult,
)
from runtime.seam_aware_recognition_result import (
    assemble_seam_aware_recognition_result,
)


def make_base_result() -> RecognitionResult:
    return RecognitionResult(
        recognition_id="RR-003",
        recognition_unit_id="RU-003",
        orientation=BasinOrientation(
            primary_basin="REC-002",
        ),
        resolution_state="oriented",
        residual_observations=[],
        provenance=Provenance(
            ingress_payload_id="ING-003",
            contract_version="3.0.0",
        ),
    )


def make_resolution(
    *,
    state: str = "SEAM_ACTIVE",
) -> OrientationResolution:
    active_seam = (
        ActiveSeam(
            seam_id="SAC-003",
            participating_basins=(
                "REC-002",
                "REC-007",
            ),
            score_gap=0.06,
        )
        if state == "SEAM_ACTIVE"
        else None
    )

    return OrientationResolution(
        resolution_id="ORES-003",
        selection_id="BSEL-003",
        seam_condition_id="SAC-003",
        primary_basin="REC-002",
        resolution_state=state,
        active_seam=active_seam,
    )


def test_assembler_emits_seam_aware_result():
    result = assemble_seam_aware_recognition_result(
        base_result=make_base_result(),
        orientation_resolution=make_resolution(),
    )

    assert result.primary_basin == "REC-002"
    assert result.resolution_state == "SEAM_ACTIVE"
    assert result.active_seam is not None
    assert result.base_result.recognition_id == "RR-003"


def test_assembler_preserves_oriented_state_without_active_seam():
    result = assemble_seam_aware_recognition_result(
        base_result=make_base_result(),
        orientation_resolution=make_resolution(
            state="ORIENTED"
        ),
    )

    assert result.resolution_state == "ORIENTED"
    assert result.active_seam is None


def test_seam_aware_result_identity_is_reproducible():
    base_result = make_base_result()
    resolution = make_resolution()

    first = assemble_seam_aware_recognition_result(
        base_result=base_result,
        orientation_resolution=resolution,
    )

    second = assemble_seam_aware_recognition_result(
        base_result=base_result,
        orientation_resolution=resolution,
    )

    assert first == second
    assert first.result_id == second.result_id


def test_assembler_rejects_primary_basin_disagreement():
    resolution = replace(
        make_resolution(),
        primary_basin="REC-007",
    )

    with pytest.raises(
        ConstitutionalViolationError,
        match="primary basins do not match",
    ):
        assemble_seam_aware_recognition_result(
            base_result=make_base_result(),
            orientation_resolution=resolution,
        )


def test_assembler_does_not_mutate_base_result():
    base_result = make_base_result()

    assemble_seam_aware_recognition_result(
        base_result=base_result,
        orientation_resolution=make_resolution(),
    )

    assert base_result.resolution_state == "oriented"
    assert base_result.orientation.primary_basin == "REC-002"
