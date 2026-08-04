from runtime.ingress_payload import GovernedIngressPayload


def test_ingress_payload_digest_is_deterministic():
    first = GovernedIngressPayload(
        payload_id="ING-001",
        raw_observation="My system won't shut off.",
        source_type="user_report",
    )

    second = GovernedIngressPayload(
        payload_id="ING-001",
        raw_observation="My system won't shut off.",
        source_type="user_report",
    )

    assert first.digest() == second.digest()


def test_ingress_payload_digest_changes_when_observation_changes():
    first = GovernedIngressPayload(
        payload_id="ING-001",
        raw_observation="My system won't shut off.",
        source_type="user_report",
    )

    second = GovernedIngressPayload(
        payload_id="ING-001",
        raw_observation="My thoughts feel heavy.",
        source_type="user_report",
    )

    assert first.digest() != second.digest()
