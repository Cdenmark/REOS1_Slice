from dataclasses import FrozenInstanceError

import pytest

from runtime.movement_types import (
    FrozenRecognitionBundle,
    RecognitionArtifactBinding,
    RecognitionArtifactKind,
)


@pytest.fixture
def valid_bindings() -> tuple[
    RecognitionArtifactBinding,
    ...,
]:
    return (
        RecognitionArtifactBinding(
            artifact_kind="CANDIDATE_BASIN_EVALUATION",
            artifact_id="CBE-001",
            artifact_digest="a" * 64,
        ),
        RecognitionArtifactBinding(
            artifact_kind="BASIN_SELECTION",
            artifact_id="BS-001",
            artifact_digest="b" * 64,
        ),
        RecognitionArtifactBinding(
            artifact_kind="SEAM_ACTIVATION_CONDITION",
            artifact_id="SAC-001",
            artifact_digest="c" * 64,
        ),
        RecognitionArtifactBinding(
            artifact_kind="ORIENTATION_RESOLUTION",
            artifact_id="OR-001",
            artifact_digest="d" * 64,
        ),
        RecognitionArtifactBinding(
            artifact_kind="SEAM_AWARE_RECOGNITION_RESULT",
            artifact_id="SARR-001",
            artifact_digest="e" * 64,
        ),
    )


@pytest.fixture
def valid_frozen_bundle(
    valid_bindings: tuple[
        RecognitionArtifactBinding,
        ...,
    ],
) -> FrozenRecognitionBundle:
    return FrozenRecognitionBundle(
        bundle_id="FRB-001",
        recognition_unit_id="RU-001",
        candidate_evaluation_ref="CBE-001",
        basin_selection_ref="BS-001",
        seam_activation_condition_ref="SAC-001",
        orientation_resolution_ref="OR-001",
        seam_aware_result_ref="SARR-001",
        artifact_bindings=valid_bindings,
        recognition_checkpoint_digest="f" * 64,
        deterministic=True,
    )


def test_controlled_recognition_artifact_kind_literal():
    kinds = RecognitionArtifactKind.__args__

    assert kinds == (
        "CANDIDATE_BASIN_EVALUATION",
        "BASIN_SELECTION",
        "SEAM_ACTIVATION_CONDITION",
        "ORIENTATION_RESOLUTION",
        "SEAM_AWARE_RECOGNITION_RESULT",
    )


def test_recognition_artifact_binding_creation(
    valid_bindings: tuple[
        RecognitionArtifactBinding,
        ...,
    ],
):
    selection_binding = valid_bindings[1]

    assert (
        selection_binding.artifact_kind
        == "BASIN_SELECTION"
    )
    assert selection_binding.artifact_id == "BS-001"
    assert selection_binding.artifact_digest == "b" * 64


def test_frozen_recognition_bundle_creation(
    valid_frozen_bundle: FrozenRecognitionBundle,
):
    assert valid_frozen_bundle.bundle_id == "FRB-001"
    assert (
        valid_frozen_bundle.recognition_unit_id
        == "RU-001"
    )

    assert (
        valid_frozen_bundle.candidate_evaluation_ref
        == "CBE-001"
    )
    assert (
        valid_frozen_bundle.basin_selection_ref
        == "BS-001"
    )
    assert (
        valid_frozen_bundle.seam_activation_condition_ref
        == "SAC-001"
    )
    assert (
        valid_frozen_bundle.orientation_resolution_ref
        == "OR-001"
    )
    assert (
        valid_frozen_bundle.seam_aware_result_ref
        == "SARR-001"
    )

    assert (
        valid_frozen_bundle.recognition_checkpoint_digest
        == "f" * 64
    )
    assert valid_frozen_bundle.deterministic is True


def test_artifact_bindings_are_immutable_tuple(
    valid_frozen_bundle: FrozenRecognitionBundle,
):
    assert isinstance(
        valid_frozen_bundle.artifact_bindings,
        tuple,
    )
    assert len(
        valid_frozen_bundle.artifact_bindings
    ) == 5


def test_movement_nouns_are_immutable(
    valid_frozen_bundle: FrozenRecognitionBundle,
    valid_bindings: tuple[
        RecognitionArtifactBinding,
        ...,
    ],
):
    with pytest.raises(FrozenInstanceError):
        valid_frozen_bundle.bundle_id = "FRB-MUTATED"

    with pytest.raises(FrozenInstanceError):
        valid_frozen_bundle.basin_selection_ref = (
            "BS-MUTATED"
        )

    with pytest.raises(FrozenInstanceError):
        valid_bindings[0].artifact_digest = "0" * 64


def test_movement_nouns_contain_no_embedded_runtime_behavior():
    prohibited_methods = {
        "create",
        "bind",
        "build",
        "generate",
        "validate",
        "verify",
        "calculate_digest",
        "derive_digest",
        "check_lineage",
        "check_parity",
    }

    assert prohibited_methods.isdisjoint(
        FrozenRecognitionBundle.__dict__
    )
    assert prohibited_methods.isdisjoint(
        RecognitionArtifactBinding.__dict__
    )
