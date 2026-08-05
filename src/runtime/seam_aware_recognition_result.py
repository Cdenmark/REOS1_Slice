from dataclasses import dataclass
from typing import Optional

from runtime.executor import ConstitutionalViolationError
from runtime.orientation_resolution import (
    ActiveSeam,
    OrientationResolution,
)
from runtime.recognition_result import RecognitionResult
from runtime.serializer import canonical_hash


@dataclass(frozen=True)
class SeamAwareRecognitionResult:
    """
    Immutable VS003 recognition output.

    This object preserves the complete frozen VS002 RecognitionResult
    and binds it to the independently resolved VS003 orientation state.

    It does not reinterpret selection, seam detection, or orientation.
    """

    result_id: str
    base_result: RecognitionResult
    orientation_resolution_id: str
    primary_basin: str
    resolution_state: str
    active_seam: Optional[ActiveSeam]


def assemble_seam_aware_recognition_result(
    base_result: RecognitionResult,
    orientation_resolution: OrientationResolution,
) -> SeamAwareRecognitionResult:
    """
    Bind an existing RecognitionResult to an OrientationResolution.

    Jurisdiction:
    - validate agreement between frozen VS002 output and VS003 resolution;
    - preserve the selected primary basin;
    - expose ORIENTED or SEAM_ACTIVE without mutating the base result.

    Prohibited:
    - changing the primary basin;
    - detecting or recalculating a seam;
    - changing the base RecognitionResult;
    - executing downstream remedy logic.
    """
    if (
        base_result.orientation.primary_basin
        != orientation_resolution.primary_basin
    ):
        raise ConstitutionalViolationError(
            "Base RecognitionResult and OrientationResolution "
            "primary basins do not match."
        )

    result_material = {
        "base_recognition_id": base_result.recognition_id,
        "orientation_resolution_id": (
            orientation_resolution.resolution_id
        ),
        "primary_basin": orientation_resolution.primary_basin,
        "resolution_state": orientation_resolution.resolution_state,
        "active_seam": (
            {
                "seam_id": orientation_resolution.active_seam.seam_id,
                "participating_basins": list(
                    orientation_resolution.active_seam.participating_basins
                ),
                "score_gap": orientation_resolution.active_seam.score_gap,
            }
            if orientation_resolution.active_seam is not None
            else None
        ),
    }

    return SeamAwareRecognitionResult(
        result_id=(
            "SARR-"
            + canonical_hash(result_material)[:16].upper()
        ),
        base_result=base_result,
        orientation_resolution_id=(
            orientation_resolution.resolution_id
        ),
        primary_basin=orientation_resolution.primary_basin,
        resolution_state=orientation_resolution.resolution_state,
        active_seam=orientation_resolution.active_seam,
    )
