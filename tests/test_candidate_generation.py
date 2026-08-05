import pytest

from runtime.candidate_generation import generate_candidate_basins
from runtime.executor import ConstitutionalViolationError
from runtime.ingress_payload import GovernedIngressPayload
from runtime.recognition_unit import instantiate_recognition_unit


def make_unit(observation: str):
    payload = GovernedIngressPayload(
        payload_id="ING-001",
        raw_observation=observation,
        source_type="user_report",
    )

    return instantiate_recognition_unit(payload)


def test_generator_discovers_topologically_eligible_basins():
    result = generate_candidate_basins(
        make_unit("My system won't shut off.")
    )

    assert [
        candidate.basin_id
        for candidate in result.candidates
    ] == [
        "REC-002",
        "REC-007",
    ]


def test_generator_records_eligibility_basis():
    result = generate_candidate_basins(
        make_unit("My system won't shut off.")
    )

    rec002 = next(
        candidate
        for candidate in result.candidates
        if candidate.basin_id == "REC-002"
    )

    assert "phrase:shut off" in rec002.eligibility_basis
    assert "mechanic:governor_failure" in rec002.eligibility_basis


def test_generator_identity_is_reproducible():
    unit = make_unit("My system won't shut off.")

    first = generate_candidate_basins(unit)
    second = generate_candidate_basins(unit)

    assert first == second
    assert first.generation_id == second.generation_id


def test_generator_fails_closed_with_insufficient_candidates():
    with pytest.raises(
        ConstitutionalViolationError,
        match="at least two eligible basins",
    ):
        generate_candidate_basins(
            make_unit("My thoughts feel heavy.")
        )