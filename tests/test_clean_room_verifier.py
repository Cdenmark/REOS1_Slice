from dataclasses import replace

import pytest

from contracts.transition_contract import (
    AuthorityMetadata,
    TransitionContract,
)
from runtime.ingress_payload import GovernedIngressPayload
from runtime.reos001 import REOS001Runtime
from verifier.clean_room import (
    VerificationError,
    verify_reos001,
)


def make_contract() -> TransitionContract:
    return TransitionContract(
        contract_id="CONTRACT-REOS-001",
        transition_id="REOS-001",
        authority=AuthorityMetadata(
            declaration_id="REOS-001",
            declaration_hash="a" * 64,
            compiler_release="compiler-0.1.0",
            compiler_digest="b" * 64,
            generated_at="2026-08-04T18:00:00+00:00",
        ),
        constitution_version="2.0.0",
        contract_version="1.0.0",
        allowed_operations=[
            "ingress_hash",
            "instantiate_recognition_unit",
            "determine_primary_basin",
        ],
        permitted_exports=[
            "recognition_result",
            "transition_telemetry",
        ],
        prohibited_exports=[
            "remedy_selection",
            "protocol_generation",
        ],
    )


def make_payload() -> GovernedIngressPayload:
    return GovernedIngressPayload(
        payload_id="ING-001",
        raw_observation="My system won't shut off.",
        source_type="user_report",
    )


def test_clean_room_verifier_reproduces_execution():
    contract = make_contract()
    payload = make_payload()

    result, telemetry = REOS001Runtime().execute(
        contract=contract,
        payload=payload,
    )

    assert verify_reos001(
        contract=contract,
        payload=payload,
        result=result,
        telemetry=telemetry,
    )


def test_clean_room_verifier_rejects_mutated_result():
    contract = make_contract()
    payload = make_payload()

    result, telemetry = REOS001Runtime().execute(
        contract=contract,
        payload=payload,
    )

    mutated_result = replace(
        result,
        recognition_id="RR-TAMPERED",
    )

    with pytest.raises(
        VerificationError,
        match="recognition_id",
    ):
        verify_reos001(
            contract=contract,
            payload=payload,
            result=mutated_result,
            telemetry=telemetry,
        )
