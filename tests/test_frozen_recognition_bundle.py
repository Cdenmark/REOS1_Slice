from dataclasses import FrozenInstanceError, fields

import pytest

from runtime.movement_types import (
    FrozenRecognitionBundle,
    RecognitionArtifactBinding,
)


def make_binding(
    *,
    kind: str = "candidate_basin_evaluation",
    artifact_id: str = "CBE-001",
    artifact_digest: str = "a" * 64,
) -> RecognitionArtifactBinding:
    return RecognitionArtifactBinding(
        artifact_kind=kind,
        artifact_id=artifact_id,
        artifact_digest=artifact_digest,
    )


def make_bundle(
    artifact_bindings=(
        make_binding(
            kind="candidate_basin_evaluation",
            artifact_id="CBE-001",
            artifact_digest="a" * 64,
        ),
        make_binding(
            kind="seam_activation_condition",
            artifact_id="SAC-001",
            artifact_digest="b" * 64,
        ),
        make_binding(
            kind="orientation_resolution",
            artifact_id="OR-001",
            artifact_digest="c" * 64,
        ),
        make_binding(
            kind="seam_aware_recognition_result",
            artifact_id="SARR-001",
            artifact_digest="d" * 64,
        ),
    ),
) -> FrozenRecognitionBundle:
    return FrozenRecognitionBundle(
        bundle_id="FRB-001",
        recognition_unit_id="RU-001",
        seam_aware_result_ref="SARR-001",
        orientation_resolution_ref="OR-001",
        candidate_evaluation_ref="CBE-001",
        seam_activation_condition_ref="SAC-001",
        artifact_bindings=artifact_bindings,
        recognition_checkpoint_digest="z" * 64,
    )


def test_controlled_recognition_artifact_kind_literal():
    with pytest.raises(
        ValueError,
        match="artifact_kind must be one of",
    ):
        make_binding(kind="invalid_artifact_kind")


def test_recognition_artifact_binding_creation():
    binding = make_binding(
        kind="orientation_resolution",
        artifact_id="OR-001",
    )

    assert binding.artifact_kind == "orientation_resolution"
    assert binding.artifact_id == "OR-001"


def test_frozen_recognition_bundle_creation():
    bundle = make_bundle()

    assert bundle.bundle_id == "FRB-001"
    assert bundle.recognition_unit_id == "RU-001"
    assert bundle.seam_aware_result_ref == "SARR-001"
    assert isinstance(bundle.artifact_bindings, tuple)
    assert len(bundle.artifact_bindings) == 4


def test_artifact_bindings_must_be_tuple():
    with pytest.raises(
        TypeError,
        match="artifact_bindings must be a tuple",
    ):
        make_bundle(
            artifact_bindings=[
                make_binding(),
            ],
        )


def test_movement_nouns_are_immutable():
    binding = make_binding()

    with pytest.raises(FrozenInstanceError):
        binding.artifact_id = "CBE-CHANGED"

    bundle = make_bundle()

    with pytest.raises(FrozenInstanceError):
        bundle.bundle_id = "FRB-CHANGED"


def test_movement_nouns_contain_no_embedded_runtime_behavior():
    noun_types = (
        RecognitionArtifactBinding,
        FrozenRecognitionBundle,
    )

    prohibited_methods = {
        "create",
        "generate",
        "evaluate",
        "qualify",
        "execute",
        "mutate",
        "reinterpret",
    }

    for noun_type in noun_types:
        assert prohibited_methods.isdisjoint(
            set(noun_type.__dict__)
        )

        assert len(fields(noun_type)) > 0
