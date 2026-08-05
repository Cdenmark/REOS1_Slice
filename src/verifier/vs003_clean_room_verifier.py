from dataclasses import dataclass
from typing import Any, Dict, Tuple


class VS003VerificationError(Exception):
    """Raised when independent VS003 verification fails."""


@dataclass(frozen=True)
class VS003VerificationCheck:
    """
    One independently evaluated constitutional assertion.
    """

    check_name: str
    passed: bool


@dataclass(frozen=True)
class VS003VerificationReport:
    """
    Immutable output of VS003 clean-room verification.

    This report records independently verified state, lineage,
    compiler-parameter application, and identifier validity.

    It does not execute runtime logic or recreate runtime identities.
    """

    report_id: str
    verifier_version: str
    evaluation_id: str
    selection_id: str
    seam_condition_id: str
    orientation_resolution_id: str
    verified: bool
    checks: Tuple[VS003VerificationCheck, ...]


VERIFIER_VERSION = "vs003-clean-room-0.1.0"


def _require_mapping(
    value: Any,
    artifact_name: str,
) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise VS003VerificationError(
            f"{artifact_name} must be a serialized dictionary."
        )

    return value


def _require_identifier(
    value: Any,
    *,
    prefix: str,
    field_name: str,
) -> str:
    if not isinstance(value, str) or not value.startswith(prefix):
        raise VS003VerificationError(
            f"{field_name} possesses invalid identifier structure."
        )

    return value


def _read_seam_parameters(
    contract_noun: Dict[str, Any],
) -> Dict[str, Any]:
    operation_parameters = contract_noun.get(
        "operation_parameters"
    )

    if not isinstance(operation_parameters, dict):
        raise VS003VerificationError(
            "Contract artifact is missing operation_parameters."
        )

    seam_parameters = operation_parameters.get(
        "detect_seam_activation"
    )

    if not isinstance(seam_parameters, dict):
        raise VS003VerificationError(
            "Contract artifact is missing detect_seam_activation parameters."
        )

    required_keys = {
        "maximum_score_gap",
        "minimum_top_score",
        "required_participant_count",
    }

    missing_keys = required_keys.difference(seam_parameters)

    if missing_keys:
        raise VS003VerificationError(
            "Contract seam parameters are incomplete: "
            + ", ".join(sorted(missing_keys))
        )

    return seam_parameters


def _derive_expected_seam_state(
    evaluation_noun: Dict[str, Any],
    seam_parameters: Dict[str, Any],
) -> str:
    candidates = evaluation_noun.get("candidates")

    if not isinstance(candidates, (list, tuple)):
        raise VS003VerificationError(
            "Candidate evaluation artifact is missing candidates."
        )

    required_participant_count = seam_parameters[
        "required_participant_count"
    ]

    if required_participant_count != 2:
        raise VS003VerificationError(
            "VS003 clean-room verification requires exactly two seam participants."
        )

    if len(candidates) < required_participant_count:
        return "UNACTIVATED"

    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise VS003VerificationError(
                "Candidate evaluation contains a non-dictionary candidate."
            )

        if "basin_id" not in candidate:
            raise VS003VerificationError(
                "Candidate evaluation contains a candidate without basin_id."
            )

        if "evidence_score" not in candidate:
            raise VS003VerificationError(
                "Candidate evaluation contains a candidate without evidence_score."
            )

    ordered_candidates = sorted(
        candidates,
        key=lambda candidate: (
            -candidate["evidence_score"],
            candidate["basin_id"],
        ),
    )

    top = ordered_candidates[0]
    secondary = ordered_candidates[1]

    leading_score = top["evidence_score"]
    secondary_score = secondary["evidence_score"]
    score_gap = leading_score - secondary_score

    maximum_score_gap = seam_parameters[
        "maximum_score_gap"
    ]

    minimum_top_score = seam_parameters[
        "minimum_top_score"
    ]

    if (
        leading_score >= minimum_top_score
        and score_gap <= maximum_score_gap
    ):
        return "ACTIVATED"

    return "UNACTIVATED"


def verify_vs003_transition(
    *,
    evaluation_noun: Dict[str, Any],
    selection_noun: Dict[str, Any],
    contract_noun: Dict[str, Any],
    witnessed_seam_noun: Dict[str, Any],
    witnessed_orientation_noun: Dict[str, Any],
) -> VS003VerificationReport:
    """
    Independently verify VS003 state and lineage.

    Identity construction is not reproduced.
    Existing identifiers are checked only for presence, prefix validity,
    and lineage continuity.
    """
    evaluation_noun = _require_mapping(
        evaluation_noun,
        "CandidateBasinEvaluation",
    )

    selection_noun = _require_mapping(
        selection_noun,
        "BasinSelection",
    )

    contract_noun = _require_mapping(
        contract_noun,
        "TransitionContract",
    )

    witnessed_seam_noun = _require_mapping(
        witnessed_seam_noun,
        "SeamActivationCondition",
    )

    witnessed_orientation_noun = _require_mapping(
        witnessed_orientation_noun,
        "OrientationResolution",
    )

    evaluation_id = _require_identifier(
        evaluation_noun.get("evaluation_id"),
        prefix="CBE-",
        field_name="evaluation_id",
    )

    recognition_unit_id = _require_identifier(
        evaluation_noun.get("recognition_unit_id"),
        prefix="RU-",
        field_name="recognition_unit_id",
    )

    selection_id = _require_identifier(
        selection_noun.get("selection_id"),
        prefix="BSEL-",
        field_name="selection_id",
    )

    seam_condition_id = _require_identifier(
        witnessed_seam_noun.get("condition_id"),
        prefix="SAC-",
        field_name="condition_id",
    )

    orientation_resolution_id = _require_identifier(
        witnessed_orientation_noun.get("resolution_id"),
        prefix="ORES-",
        field_name="resolution_id",
    )

    if selection_noun.get("evaluation_id") != evaluation_id:
        raise VS003VerificationError(
            "Lineage mismatch: BasinSelection does not reference "
            "the supplied CandidateBasinEvaluation."
        )

    if (
        witnessed_seam_noun.get("evaluation_id")
        != evaluation_id
    ):
        raise VS003VerificationError(
            "Lineage mismatch: SeamActivationCondition does not "
            "reference the supplied CandidateBasinEvaluation."
        )

    if (
        witnessed_seam_noun.get("recognition_unit_id")
        != recognition_unit_id
    ):
        raise VS003VerificationError(
            "Lineage mismatch: SeamActivationCondition does not "
            "reference the supplied RecognitionUnit."
        )

    if (
        witnessed_orientation_noun.get("selection_id")
        != selection_id
    ):
        raise VS003VerificationError(
            "Lineage mismatch: OrientationResolution does not "
            "reference the supplied BasinSelection."
        )

    if (
        witnessed_orientation_noun.get("seam_condition_id")
        != seam_condition_id
    ):
        raise VS003VerificationError(
            "Lineage mismatch: OrientationResolution does not "
            "reference the supplied SeamActivationCondition."
        )

    selected_primary_basin = selection_noun.get(
        "primary_basin"
    )

    if (
        witnessed_orientation_noun.get("primary_basin")
        != selected_primary_basin
    ):
        raise VS003VerificationError(
            "OrientationResolution changes the selected primary basin."
        )

    seam_parameters = _read_seam_parameters(
        contract_noun
    )

    expected_seam_state = _derive_expected_seam_state(
        evaluation_noun,
        seam_parameters,
    )

    witnessed_seam_state = witnessed_seam_noun.get(
        "activation_state"
    )

    if witnessed_seam_state != expected_seam_state:
        raise VS003VerificationError(
            "Seam state verification failure: "
            f"derived '{expected_seam_state}', "
            f"witnessed '{witnessed_seam_state}'."
        )

    expected_orientation_state = (
        "SEAM_ACTIVE"
        if expected_seam_state == "ACTIVATED"
        else "ORIENTED"
    )

    witnessed_orientation_state = (
        witnessed_orientation_noun.get(
            "resolution_state"
        )
    )

    if (
        witnessed_orientation_state
        != expected_orientation_state
    ):
        raise VS003VerificationError(
            "Orientation state verification failure: "
            f"derived '{expected_orientation_state}', "
            f"witnessed '{witnessed_orientation_state}'."
        )

    checks = (
        VS003VerificationCheck(
            check_name="evaluation_identifier_valid",
            passed=True,
        ),
        VS003VerificationCheck(
            check_name="selection_identifier_valid",
            passed=True,
        ),
        VS003VerificationCheck(
            check_name="seam_identifier_valid",
            passed=True,
        ),
        VS003VerificationCheck(
            check_name="orientation_identifier_valid",
            passed=True,
        ),
        VS003VerificationCheck(
            check_name="selection_evaluation_lineage",
            passed=True,
        ),
        VS003VerificationCheck(
            check_name="seam_evaluation_lineage",
            passed=True,
        ),
        VS003VerificationCheck(
            check_name="seam_recognition_unit_lineage",
            passed=True,
        ),
        VS003VerificationCheck(
            check_name="orientation_selection_lineage",
            passed=True,
        ),
        VS003VerificationCheck(
            check_name="orientation_seam_lineage",
            passed=True,
        ),
        VS003VerificationCheck(
            check_name="primary_basin_preserved",
            passed=True,
        ),
        VS003VerificationCheck(
            check_name="compiler_parameters_applied",
            passed=True,
        ),
        VS003VerificationCheck(
            check_name="seam_state_verified",
            passed=True,
        ),
        VS003VerificationCheck(
            check_name="orientation_state_verified",
            passed=True,
        ),
    )

    report_material = "|".join(
        [
            VERIFIER_VERSION,
            evaluation_id,
            selection_id,
            seam_condition_id,
            orientation_resolution_id,
            expected_seam_state,
            expected_orientation_state,
        ]
    )

    import hashlib

    report_digest = hashlib.sha256(
        report_material.encode("utf-8")
    ).hexdigest()

    return VS003VerificationReport(
        report_id=(
            "VR3-"
            + report_digest[:16].upper()
        ),
        verifier_version=VERIFIER_VERSION,
        evaluation_id=evaluation_id,
        selection_id=selection_id,
        seam_condition_id=seam_condition_id,
        orientation_resolution_id=(
            orientation_resolution_id
        ),
        verified=True,
        checks=checks,
    )
