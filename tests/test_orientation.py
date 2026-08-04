import pytest

from runtime.executor import ConstitutionalViolationError
from runtime.ingress_payload import GovernedIngressPayload
from runtime.orientation import determine_primary_basin
from runtime.recognition_unit import instantiate_recognition_unit


def make_unit(observation: str):
    payload = GovernedIngressPayload(
        payload_id="ING-001",
        raw_observation=observation,
        source_type="user_report",
    )

    return instantiate_recognition_unit(payload)


def test_orientation_maps_shut_off_observation_to_rec002():
    orientation = determine_primary_basin(
        make_unit("My system won't shut off.")
    )

    assert orientation.primary_basin == "REC-002"
    assert orientation.active_seam is None


def test_orientation_is_case_insensitive():
    orientation = determine_primary_basin(
        make_unit("MY SYSTEM WON'T SHUT OFF.")
    )

    assert orientation.primary_basin == "REC-002"


def test_orientation_fails_closed_when_no_match_exists():
    with pytest.raises(
        ConstitutionalViolationError,
        match="No deterministic basin orientation",
    ):
        determine_primary_basin(
            make_unit("My thoughts feel heavy.")
        )
