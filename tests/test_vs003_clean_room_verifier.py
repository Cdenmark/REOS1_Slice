from dataclasses import asdict, replace

import pytest

from contracts.transition_contract import (
    AuthorityMetadata,
    TransitionContract,
)
from runtime.basin_selector import select_primary_basin
from runtime.candidate_basin_evaluation import (
    CandidateBasin,
    CandidateBasinEvaluation,
)
from runtime.ingress_payload import GovernedIngressPayload
from runtime.orientation_resolution import resolve_orientation
from runtime.recognition_unit import instantiate_recognition_unit
from runtime.seam_activation import (
    SeamDetectionParameters,
    detect_seam_activation,
)
from verifier.vs003_clean_room_verifier import (
    VS003VerificationError,
    verify_vs003_transition,
)


def make_contract(
    *,
    maximum_score_gap: float = 0.10,
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
        allowed_operations=[
            "detect_seam_activation",
            "resolve_orientation",
        ],
        permitted_exports=[
            "seam_activation_condition",
            "orientation_resolution",
        ],
        prohibited_exports=[],
        operation_parameters={
            "detect_seam_activation": {
                "maximum_score_gap": maximum_score_gap,
                "minimum_top_score": 0.50,
                "required_participant_count": 2,
            }
        },
    )


def make_artifacts(
    *,
    primary_score: float = 0.82,
    secondary_score: float = 0.76,
    maximum_score_gap: float = 0.10,
):
    contract = make_contract(
        maximum_score_gap=maximum_score_gap
    )

    payload = GovernedIngressPayload(
        payload_id="ING-003",
        raw_observation="My system won't shut off.",
        source_type="user_report",
    )

    unit = instantiate_recognition_unit(payload)

    evaluation = CandidateBasinEvaluation(
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

    selection = select_primary_basin(evaluation)

    seam_condition = detect_seam_activation(
        evaluation=evaluation,
        recognition_unit=unit,
        contract=contract,
        parameters=SeamDetectionParameters(
            maximum_score_gap=maximum_score_gap,
            minimum_top_score=0.50,
            required_participant_count=2,
        ),
    )

    orientation_resolution = resolve_orientation(
        selection=selection,
        seam_condition=seam_condition,
    )

    return (
        contract,
        evaluation,
        selection,
        seam_condition,
        orientation_resolution,
    )


def verify_artifacts(artifacts):
    (
        contract,
        evaluation,
        selection,
        seam_condition,
        orientation_resolution,
    ) = artifacts

    return verify_vs003_transition(
        evaluation_noun=asdict(evaluation),
        selection_noun=asdict(selection),
        contract_noun=asdict(contract),
        witnessed_seam_noun=asdict(
            seam_condition
        ),
        witnessed_orientation_noun=asdict(
            orientation_resolution
        ),
    )


def test_clean_room_verifier_accepts_valid_seam_active_state():
    report = verify_artifacts(
        make_artifacts(
            primary_score=0.82,
            secondary_score=0.76,
            maximum_score_gap=0.10,
        )
    )

    assert report.verified is True
    assert report.report_id.startswith("VR3-")
    assert all(check.passed for check in report.checks)


def test_clean_room_verifier_accepts_valid_oriented_state():
    report = verify_artifacts(
        make_artifacts(
            primary_score=0.92,
            secondary_score=0.54,
            maximum_score_gap=0.10,
        )
    )

    assert report.verified is True


def test_clean_room_verifier_rejects_lineage_mismatch():
    artifacts = make_artifacts()

    (
        contract,
        evaluation,
        selection,
        seam_condition,
        orientation_resolution,
    ) = artifacts

    mismatched_seam = replace(
        seam_condition,
        evaluation_id="CBE-DIFFERENT",
    )

    with pytest.raises(
        VS003VerificationError,
        match="Lineage mismatch",
    ):
        verify_vs003_transition(
            evaluation_noun=asdict(evaluation),
            selection_noun=asdict(selection),
            contract_noun=asdict(contract),
            witnessed_seam_noun=asdict(
                mismatched_seam
            ),
            witnessed_orientation_noun=asdict(
                orientation_resolution
            ),
        )


def test_clean_room_verifier_rejects_tampered_seam_state():
    artifacts = make_artifacts()

    (
        contract,
        evaluation,
        selection,
        seam_condition,
        orientation_resolution,
    ) = artifacts

    tampered_seam = replace(
        seam_condition,
        activation_state="UNACTIVATED",
    )

    with pytest.raises(
        VS003VerificationError,
        match="Seam state verification failure",
    ):
        verify_vs003_transition(
            evaluation_noun=asdict(evaluation),
            selection_noun=asdict(selection),
            contract_noun=asdict(contract),
            witnessed_seam_noun=asdict(
                tampered_seam
            ),
            witnessed_orientation_noun=asdict(
                orientation_resolution
            ),
        )


def test_clean_room_verifier_rejects_tampered_orientation_state():
    artifacts = make_artifacts()

    (
        contract,
        evaluation,
        selection,
        seam_condition,
        orientation_resolution,
    ) = artifacts

    tampered_orientation = replace(
        orientation_resolution,
        resolution_state="ORIENTED",
        active_seam=None,
    )

    with pytest.raises(
        VS003VerificationError,
        match="Orientation state verification failure",
    ):
        verify_vs003_transition(
            evaluation_noun=asdict(evaluation),
            selection_noun=asdict(selection),
            contract_noun=asdict(contract),
            witnessed_seam_noun=asdict(
                seam_condition
            ),
            witnessed_orientation_noun=asdict(
                tampered_orientation
            ),
        )


def test_clean_room_verifier_rejects_missing_contract_parameters():
    artifacts = make_artifacts()

    (
        contract,
        evaluation,
        selection,
        seam_condition,
        orientation_resolution,
    ) = artifacts

    contract_noun = asdict(contract)
    contract_noun["operation_parameters"] = {}

    with pytest.raises(
        VS003VerificationError,
        match="missing detect_seam_activation parameters",
    ):
        verify_vs003_transition(
            evaluation_noun=asdict(evaluation),
            selection_noun=asdict(selection),
            contract_noun=contract_noun,
            witnessed_seam_noun=asdict(
                seam_condition
            ),
            witnessed_orientation_noun=asdict(
                orientation_resolution
            ),
        )


def test_clean_room_verifier_identity_is_reproducible():
    artifacts = make_artifacts()

    first = verify_artifacts(artifacts)
    second = verify_artifacts(artifacts)

    assert first == second
    assert first.report_id == second.report_id
