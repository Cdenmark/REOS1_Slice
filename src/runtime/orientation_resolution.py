from dataclasses import dataclass
from typing import Literal, Optional, Tuple

from runtime.basin_selector import BasinSelection
from runtime.executor import ConstitutionalViolationError
from runtime.seam_activation import SeamActivationCondition
from runtime.serializer import canonical_hash


OrientationState = Literal[
    "ORIENTED",
    "SEAM_ACTIVE",
]


@dataclass(frozen=True)
class ActiveSeam:
    """
    Immutable reference to the activated boundary relationship.

    This object does not detect or evaluate the seam.
    It preserves the seam relationship inside final orientation.
    """

    seam_id: str
    participating_basins: Tuple[str, ...]
    score_gap: float


@dataclass(frozen=True)
class OrientationResolution:
    """
    Immutable output of governed orientation resolution.

    The resolver binds an existing BasinSelection to an existing
    SeamActivationCondition.

    It cannot change basin selection, candidate scores, or seam state.
    """

    resolution_id: str
    selection_id: str
    seam_condition_id: str
    primary_basin: str
    resolution_state: OrientationState
    active_seam: Optional[ActiveSeam]


def resolve_orientation(
    selection: BasinSelection,
    seam_condition: SeamActivationCondition,
) -> OrientationResolution:
    """
    Resolve final orientation from completed selection and seam artifacts.

    Jurisdiction:
    - preserve the selected primary basin;
    - express either ORIENTED or SEAM_ACTIVE;
    - bind an activated seam into the orientation artifact.

    Prohibited:
    - changing the selected basin;
    - recalculating scores or tension;
    - activating or deactivating the seam;
    - generating new basin identities.
    """
    if selection.evaluation_id != seam_condition.evaluation_id:
        raise ConstitutionalViolationError(
            "Basin Selection and Seam Activation Condition "
            "evaluation identities do not match."
        )

    participant_ids = tuple(
        participant.basin_id
        for participant in seam_condition.participating_basins
    )

    if selection.primary_basin not in participant_ids:
        raise ConstitutionalViolationError(
            "Selected primary basin is absent from the seam participants."
        )

    if len(set(participant_ids)) != len(participant_ids):
        raise ConstitutionalViolationError(
            "Seam participants contain duplicate basin identities."
        )

    active_seam: Optional[ActiveSeam]

    if seam_condition.activation_state == "ACTIVATED":
        active_seam = ActiveSeam(
            seam_id=seam_condition.condition_id,
            participating_basins=participant_ids,
            score_gap=seam_condition.score_gap,
        )
        resolution_state: OrientationState = "SEAM_ACTIVE"
    else:
        active_seam = None
        resolution_state = "ORIENTED"

    resolution_material = {
        "selection_id": selection.selection_id,
        "seam_condition_id": seam_condition.condition_id,
        "primary_basin": selection.primary_basin,
        "resolution_state": resolution_state,
        "active_seam": (
            {
                "seam_id": active_seam.seam_id,
                "participating_basins": list(
                    active_seam.participating_basins
                ),
                "score_gap": active_seam.score_gap,
            }
            if active_seam is not None
            else None
        ),
    }

    return OrientationResolution(
        resolution_id=(
            "ORES-"
            + canonical_hash(resolution_material)[:16].upper()
        ),
        selection_id=selection.selection_id,
        seam_condition_id=seam_condition.condition_id,
        primary_basin=selection.primary_basin,
        resolution_state=resolution_state,
        active_seam=active_seam,
    )
