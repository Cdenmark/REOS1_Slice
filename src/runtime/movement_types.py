from dataclasses import dataclass
from typing import Literal, get_args


RecognitionArtifactKind = Literal[
    "candidate_basin_evaluation",
    "seam_activation_condition",
    "orientation_resolution",
    "seam_aware_recognition_result",
]


@dataclass(frozen=True)
class RecognitionArtifactBinding:
    """Immutable reference and digest for one recognition artifact."""

    artifact_kind: RecognitionArtifactKind
    artifact_id: str
    artifact_digest: str

    def __post_init__(self) -> None:
        allowed_kinds = get_args(RecognitionArtifactKind)
        if self.artifact_kind not in allowed_kinds:
            raise ValueError(
                "artifact_kind must be one of: "
                + ", ".join(allowed_kinds)
            )


@dataclass(frozen=True)
class FrozenRecognitionBundle:
    """Canonical immutable recognition boundary below the freeze line."""

    bundle_id: str
    recognition_unit_id: str
    seam_aware_result_ref: str
    orientation_resolution_ref: str
    candidate_evaluation_ref: str
    seam_activation_condition_ref: str
    artifact_bindings: tuple[RecognitionArtifactBinding, ...]
    recognition_checkpoint_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.artifact_bindings, tuple):
            raise TypeError(
                "artifact_bindings must be a tuple[RecognitionArtifactBinding, ...]"
            )
