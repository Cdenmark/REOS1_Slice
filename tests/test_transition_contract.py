from contracts.transition_contract import (
    AuthorityMetadata,
    TransitionContract,
)


def make_contract(allowed_operations: list[str]) -> TransitionContract:
    authority = AuthorityMetadata(
        declaration_id="REOS-001",
        declaration_hash="a" * 64,
        compiler_release="compiler-0.1.0",
        compiler_digest="b" * 64,
        generated_at="2026-08-04T18:00:00+00:00",
    )

    return TransitionContract(
        contract_id="CONTRACT-REOS-001",
        transition_id="REOS-001",
        authority=authority,
        constitution_version="2.0.0",
        contract_version="1.0.0",
        allowed_operations=allowed_operations,
        permitted_exports=[
            "recognition_result",
            "transition_telemetry",
        ],
        prohibited_exports=[
            "remedy_selection",
            "protocol_generation",
        ],
        operation_parameters={},
    )


def test_transition_contract_digest_is_deterministic():
    first = make_contract(
        [
            "ingress_hash",
            "instantiate_recognition_unit",
            "determine_primary_basin",
        ]
    )

    second = make_contract(
        [
            "determine_primary_basin",
            "ingress_hash",
            "instantiate_recognition_unit",
        ]
    )

    assert first.digest() == second.digest()


def test_transition_contract_digest_is_deterministic_when_generated_at_is_defaulted():
    first = TransitionContract(
        contract_id="CONTRACT-REOS-001",
        transition_id="REOS-001",
        authority=AuthorityMetadata(
            declaration_id="REOS-001",
            declaration_hash="a" * 64,
            compiler_release="compiler-0.1.0",
            compiler_digest="b" * 64,
            generated_at="1970-01-01T00:00:00+00:00",
        ),
        constitution_version="2.0.0",
        contract_version="1.0.0",
        allowed_operations=["ingress_hash"],
        permitted_exports=["recognition_result"],
        prohibited_exports=[],
        operation_parameters={},
    )

    second = TransitionContract(
        contract_id="CONTRACT-REOS-001",
        transition_id="REOS-001",
        authority=AuthorityMetadata(
            declaration_id="REOS-001",
            declaration_hash="a" * 64,
            compiler_release="compiler-0.1.0",
            compiler_digest="b" * 64,
            generated_at="1970-01-01T00:00:00+00:00",
        ),
        constitution_version="2.0.0",
        contract_version="1.0.0",
        allowed_operations=["ingress_hash"],
        permitted_exports=["recognition_result"],
        prohibited_exports=[],
        operation_parameters={},
    )

    assert first.digest() == second.digest()


def test_transition_contract_digest_changes_when_authority_changes():
    first = make_contract(["ingress_hash"])

    second = TransitionContract(
        contract_id=first.contract_id,
        transition_id=first.transition_id,
        authority=AuthorityMetadata(
            declaration_id="REOS-001",
            declaration_hash="c" * 64,
            compiler_release="compiler-0.1.0",
            compiler_digest="b" * 64,
            generated_at="2026-08-04T18:00:00+00:00",
        ),
        constitution_version=first.constitution_version,
        contract_version=first.contract_version,
        allowed_operations=first.allowed_operations,
        permitted_exports=first.permitted_exports,
        prohibited_exports=first.prohibited_exports,
        operation_parameters=first.operation_parameters,
    )

    assert first.digest() != second.digest()


def test_contract_digest_changes_when_operation_parameters_change():
    authority = AuthorityMetadata(
        declaration_id="REOS-003",
        declaration_hash="a" * 64,
        compiler_release="compiler-0.3.0",
        compiler_digest="b" * 64,
        generated_at="2026-08-05T18:00:00+00:00",
    )

    first = TransitionContract(
        contract_id="CONTRACT-REOS-003",
        transition_id="REOS-003",
        authority=authority,
        constitution_version="2.0.0",
        contract_version="3.0.0",
        allowed_operations=[
            "detect_seam_activation",
        ],
        permitted_exports=[
            "seam_activation_condition",
        ],
        prohibited_exports=[],
        operation_parameters={
            "detect_seam_activation": {
                "maximum_score_gap": 0.10,
                "minimum_top_score": 0.50,
                "required_participant_count": 2,
            }
        },
    )

    second = TransitionContract(
        contract_id="CONTRACT-REOS-003",
        transition_id="REOS-003",
        authority=authority,
        constitution_version="2.0.0",
        contract_version="3.0.0",
        allowed_operations=[
            "detect_seam_activation",
        ],
        permitted_exports=[
            "seam_activation_condition",
        ],
        prohibited_exports=[],
        operation_parameters={
            "detect_seam_activation": {
                "maximum_score_gap": 0.20,
                "minimum_top_score": 0.50,
                "required_participant_count": 2,
            }
        },
    )

    assert first.digest() != second.digest()


def test_contract_operation_parameters_are_deterministic():
    authority = AuthorityMetadata(
        declaration_id="REOS-003",
        declaration_hash="a" * 64,
        compiler_release="compiler-0.3.0",
        compiler_digest="b" * 64,
        generated_at="2026-08-05T18:00:00+00:00",
    )

    parameters = {
        "detect_seam_activation": {
            "maximum_score_gap": 0.10,
            "minimum_top_score": 0.50,
            "required_participant_count": 2,
        }
    }

    first = TransitionContract(
        contract_id="CONTRACT-REOS-003",
        transition_id="REOS-003",
        authority=authority,
        constitution_version="2.0.0",
        contract_version="3.0.0",
        allowed_operations=[
            "detect_seam_activation",
        ],
        permitted_exports=[],
        prohibited_exports=[],
        operation_parameters=parameters,
    )

    second = TransitionContract(
        contract_id="CONTRACT-REOS-003",
        transition_id="REOS-003",
        authority=authority,
        constitution_version="2.0.0",
        contract_version="3.0.0",
        allowed_operations=[
            "detect_seam_activation",
        ],
        permitted_exports=[],
        prohibited_exports=[],
        operation_parameters=parameters,
    )

    assert first.digest() == second.digest()
