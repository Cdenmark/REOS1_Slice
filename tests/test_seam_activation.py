from dataclasses import replace

import pytest

from contracts.transition_contract import (
    AuthorityMetadata,
    TransitionContract,
)
from runtime.candidate_basin_evaluation import (
    CandidateBasin,
    CandidateBasinEvaluation,
)
from runtime.executor import ConstitutionalViolationError
from runtime.ingress_payload import GovernedIngressPayload
from runtime.recognition_unit import instantiate_recognition_unit
from runtime.seam_activation import (
    SeamDetectionParameters,
    detect_seam_activation,
)


def make_contract(
    *,
    allowed_operations: list[str] | None = None,
) -> TransitionContract:
    return TransitionContract(
        contract_id="CONTRACT-REOS-003",
        transition_id="REOS-003",
        authority=AuthorityMetadata(
            declaration_id="REOS-003",
            declaration_hash="a" * 64,
            compiler_release="compiler-0.3.0",
            compiler_digest="b" * 64,
            generated_at="2026-08-05T18:00:00+00:00",
        ),
        constitution_version="2.0.0",
        contract_version="3.0.0",
        allowed_operations=(
            ["detect_seam_activation"]
            if allowed_operations is None
            else allowed_operations
        ),
        permitted_exports=[
            "seam_activation_condition",
        ],
        prohibited_exports=[
            "remedy_selection",
            "protocol_generation",
        ],
        operation_parameters={},
    )


def make_unit():
    payload = GovernedIngressPayload(
        payload_id="ING-003",
        raw_observation="My system won't shut off.",
        source_type="user_report",
    )

    return instantiate_recognition_unit(payload)


def make_evaluation(
    *,
    primary_score: float,
    secondary_score: float,
) -> CandidateBasinEvaluation:
    unit = make_unit()

    return CandidateBasinEvaluation(
        evaluation_id="CBE-003",
        recognition_unit_id=unit.recognition_unit_id,
        candidates=(
            CandidateBasin(
                basin_id="REC-002",
                evidence_score=primary_score,
            ),
            CandidateBasin(
                basin_id="REC-007",
                evidence_score=secondary_score,
            ),
        ),
    )


def make_parameters() -> SeamDetectionParameters:
    return SeamDetectionParameters(
        maximum_score_gap=0.10,
        minimum_top_score=0.50,
        required_participant_count=2,
    )


def test_seam_activates_when_score_gap_is_within_threshold():
    unit = make_unit()

    condition = detect_seam_activation(
        evaluation=make_evaluation(
            primary_score=0.82,
            secondary_score=0.76,
        ),
        recognition_unit=unit,
        contract=make_contract(),
        parameters=make_parameters(),
    )

    assert condition.activation_state == "ACTIVATED"
    assert condition.score_gap == pytest.approx(0.06)
    assert [
        participant.basin_id
        for participant in condition.participating_basins
    ] == [
        "REC-002",
        "REC-007",
    ]


def test_seam_remains_unactivated_when_gap_exceeds_threshold():
    unit = make_unit()

    condition = detect_seam_activation(
        evaluation=make_evaluation(
            primary_score=0.92,
            secondary_score=0.54,
        ),
        recognition_unit=unit,
        contract=make_contract(),
        parameters=make_parameters(),
    )

    assert condition.activation_state == "UNACTIVATED"
    assert condition.score_gap == pytest.approx(0.38)


def test_seam_requires_minimum_top_score():
    unit = make_unit()

    condition = detect_seam_activation(
        evaluation=make_evaluation(
            primary_score=0.40,
            secondary_score=0.35,
        ),
        recognition_unit=unit,
        contract=make_contract(),
        parameters=make_parameters(),
    )

    assert condition.activation_state == "UNACTIVATED"


def test_seam_detection_is_reproducible():
    unit = make_unit()
    evaluation = make_evaluation(
        primary_score=0.82,
        secondary_score=0.76,
    )

    first = detect_seam_activation(
        evaluation=evaluation,
        recognition_unit=unit,
        contract=make_contract(),
        parameters=make_parameters(),
    )

    second = detect_seam_activation(
        evaluation=evaluation,
        recognition_unit=unit,
        contract=make_contract(),
        parameters=make_parameters(),
    )

    assert first == second
    assert first.condition_id == second.condition_id


def test_seam_detector_rejects_unauthorized_operation():
    unit = make_unit()

    with pytest.raises(
        ConstitutionalViolationError,
        match="Unauthorized operation",
    ):
        detect_seam_activation(
            evaluation=make_evaluation(
                primary_score=0.82,
                secondary_score=0.76,
            ),
            recognition_unit=unit,
            contract=make_contract(
                allowed_operations=[]
            ),
            parameters=make_parameters(),
        )


def test_seam_detector_rejects_lineage_mismatch():
    unit = make_unit()
    evaluation = make_evaluation(
        primary_score=0.82,
        secondary_score=0.76,
    )

    mismatched_evaluation = replace(
        evaluation,
        recognition_unit_id="RU-DIFFERENT",
    )

    with pytest.raises(
        ConstitutionalViolationError,
        match="identities do not match",
    ):
        detect_seam_activation(
            evaluation=mismatched_evaluation,
            recognition_unit=unit,
            contract=make_contract(),
            parameters=make_parameters(),
        )


def test_seam_detector_does_not_modify_candidate_scores():
    unit = make_unit()
    evaluation = make_evaluation(
        primary_score=0.82,
        secondary_score=0.76,
    )

    original_scores = tuple(
        candidate.evidence_score
        for candidate in evaluation.candidates
    )

    detect_seam_activation(
        evaluation=evaluation,
        recognition_unit=unit,
        contract=make_contract(),
        parameters=make_parameters(),
    )

    assert tuple(
        candidate.evidence_score
        for candidate in evaluation.candidates
    ) == original_scores
