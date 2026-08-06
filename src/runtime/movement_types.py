from dataclasses import dataclass
from typing import Literal, Tuple, get_args

from foundation.topology_types import TransitionTopology


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


TopologyVerificationStatus = Literal[
    "VERIFIED",
]


@dataclass(frozen=True)
class VerifiedTopologyBundle:
    """
    Immutable boundary noun representing the sole actionable
    topology input for directional candidate generation.

    The exact verified TransitionTopology snapshot is embedded so
    unverified topology cannot re-enter downstream execution.

    The duplicated topology identity fields are audit bindings only.
    Downstream topology edges must be read exclusively from
    topology_snapshot.

    Verification, parity enforcement, digest matching, lawful
    VERIFIED-state construction, and fail-closed behavior belong
    strictly to TopologyBindingVerifier.
    """

    binding_id: str

    topology_ref: str
    topology_id: str
    topology_version: str
    topology_digest: str
    topology_snapshot: TransitionTopology

    bound_contract_id: str
    bound_contract_digest: str

    verification_state: TopologyVerificationStatus = "VERIFIED"
    deterministic: bool = True
