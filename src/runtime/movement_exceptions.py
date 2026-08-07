"""
Movement Horizon exception taxonomy for REOS-004.

Defines the fail-closed exception family used by
RecognitionCheckpointBinder. Failure meaning is carried through
declaration-controlled reason codes rather than a large exception
subclass hierarchy.
"""

from typing import Final, FrozenSet


RECOGNITION_CHECKPOINT_REASON_CODES: Final[FrozenSet[str]] = frozenset(
    {
        "MISSING_REQUIRED_ARTIFACT",
        "ARTIFACT_TYPE_MISMATCH",
        "RECOGNITION_UNIT_MISMATCH",
        "EVALUATION_LINEAGE_MISMATCH",
        "SELECTION_LINEAGE_MISMATCH",
        "SEAM_LINEAGE_MISMATCH",
        "ORIENTATION_LINEAGE_MISMATCH",
        "BASE_RESULT_RECOGNITION_UNIT_MISMATCH",
        "BASE_RESULT_SELECTION_OUTCOME_MISMATCH",
        "ARTIFACT_SET_MISMATCH",
        "DUPLICATE_ARTIFACT_KIND",
        "DUPLICATE_ARTIFACT_ID",
        "CANONICAL_SEQUENCE_VIOLATION",
        "DIGEST_CONSTRUCTION_FAILURE",
    }
)


class RecognitionCheckpointBindingError(Exception):
    """
    Base fail-closed exception for RecognitionCheckpointBinder.

    reason_code must belong to the declaration-controlled
    REOS-004 recognition checkpoint failure vocabulary.
    """

    def __init__(
        self,
        reason_code: str,
        message: str,
    ) -> None:
        if reason_code not in RECOGNITION_CHECKPOINT_REASON_CODES:
            raise ValueError(
                "Unrecognized REOS-004 recognition checkpoint "
                f"reason code: {reason_code!r}"
            )

        super().__init__(
            f"[{reason_code}] {message}"
        )

        self.reason_code = reason_code
        self.message = message


class IncompleteRecognitionCheckpointError(
    RecognitionCheckpointBindingError
):
    """
    Convenience specialization for a missing required artifact.

    Other binder failures remain within the stable base exception
    family and are distinguished by declaration-controlled
    reason_code.
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            "MISSING_REQUIRED_ARTIFACT",
            message,
        )
