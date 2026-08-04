from runtime.ingress_payload import GovernedIngressPayload
from runtime.recognition_unit import instantiate_recognition_unit


def make_payload() -> GovernedIngressPayload:
    return GovernedIngressPayload(
        payload_id="ING-001",
        raw_observation="My system won't shut off.",
        source_type="user_report",
    )


def test_recognition_unit_preserves_literal_observation():
    payload = make_payload()

    unit = instantiate_recognition_unit(payload)

    assert unit.literal_observation == payload.raw_observation
    assert unit.ingress_payload_id == payload.payload_id
    assert unit.ingress_payload_digest == payload.digest()


def test_recognition_unit_identity_is_deterministic():
    first = instantiate_recognition_unit(make_payload())
    second = instantiate_recognition_unit(make_payload())

    assert first.recognition_unit_id == second.recognition_unit_id
    assert first.digest() == second.digest()


def test_recognition_unit_identity_changes_with_payload():
    first = instantiate_recognition_unit(make_payload())

    second = instantiate_recognition_unit(
        GovernedIngressPayload(
            payload_id="ING-002",
            raw_observation="My thoughts feel heavy.",
            source_type="user_report",
        )
    )

    assert first.recognition_unit_id != second.recognition_unit_id
