import pytest

from runtime.movement_exceptions import (
    IncompleteRecognitionCheckpointError,
    RECOGNITION_CHECKPOINT_REASON_CODES,
    RecognitionCheckpointBindingError,
)


def test_recognition_checkpoint_reason_vocabulary_is_exact():
    assert RECOGNITION_CHECKPOINT_REASON_CODES == frozenset(
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


def test_binding_error_preserves_reason_code_and_message():
    error = RecognitionCheckpointBindingError(
        "SELECTION_LINEAGE_MISMATCH",
        "selection lineage mismatch",
    )

    assert error.reason_code == "SELECTION_LINEAGE_MISMATCH"
    assert error.message == "selection lineage mismatch"
    assert str(error) == (
        "[SELECTION_LINEAGE_MISMATCH] "
        "selection lineage mismatch"
    )


def test_unknown_reason_code_fails_closed():
    with pytest.raises(ValueError):
        RecognitionCheckpointBindingError(
            "RUNTIME_INVENTED_REASON",
            "must fail",
        )


def test_incomplete_checkpoint_error_uses_declared_reason():
    error = IncompleteRecognitionCheckpointError(
        "missing basin selection"
    )

    assert isinstance(
        error,
        RecognitionCheckpointBindingError,
    )
    assert (
        error.reason_code
        == "MISSING_REQUIRED_ARTIFACT"
    )
