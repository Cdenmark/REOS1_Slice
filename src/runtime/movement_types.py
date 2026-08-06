from dataclasses import dataclass
from typing import Literal, Tuple

from foundation.topology_types import TransitionTopology


RecognitionArtifactKind = Literal[
    "CANDIDATE_BASIN_EVALUATION",
    "BASIN_SELECTION",
    "SEAM_ACTIVATION_CONDITION",
    "ORIENTATION_RESOLUTION",
    "SEAM_AWARE_RECOGNITION_RESULT",
]


@dataclass(frozen=True)
class RecognitionArtifactBinding:
    """
    Immutable identity-and-digest binding for one required
    Recognition Horizon artifact.
    """

    artifact_kind: RecognitionArtifactKind
    artifact_id: str
    artifact_digest: str


@dataclass(frozen=True)
class FrozenRecognitionBundle:
    """
    Immutable boundary noun representing the sole actionable
    Recognition checkpoint below the Recognition Freeze Line.

    The explicit reference fields are named constitutional identity
    projections. The artifact_bindings tuple carries the corresponding
    content-addressed identity and digest records.

    Construction, completeness validation, reference-to-binding parity,
    lineage verification, and digest derivation belong exclusively to
    RecognitionCheckpointBinder.
    """

    bundle_id: str
    recognition_unit_id: str

    candidate_evaluation_ref: str
    basin_selection_ref: str
    seam_activation_condition_ref: str
    orientation_resolution_ref: str
    seam_aware_result_ref: str

    artifact_bindings: Tuple[
        RecognitionArtifactBinding,
        ...
    ]

    recognition_checkpoint_digest: str
    deterministic: bool = True


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
