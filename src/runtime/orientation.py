from runtime.executor import ConstitutionalViolationError
from runtime.recognition_result import BasinOrientation
from runtime.recognition_unit import RecognitionUnit


VS001_TARGET_BASIN = "REC-002"
VS001_MATCH_PHRASE = "shut off"


def determine_primary_basin(
    recognition_unit: RecognitionUnit,
) -> BasinOrientation:
    """
    Execute the bounded REOS-VS001 orientation operation.

    VS001 intentionally recognizes one deterministic phrase and emits
    one primary basin. It does not perform seam evaluation, inference,
    remedy selection, or fallback classification.
    """
    normalized_observation = recognition_unit.literal_observation.casefold()

    if VS001_MATCH_PHRASE not in normalized_observation:
        raise ConstitutionalViolationError(
            "No deterministic basin orientation exists for this observation."
        )

    return BasinOrientation(
        primary_basin=VS001_TARGET_BASIN,
        active_seam=None,
        directional_momentum=None,
    )
