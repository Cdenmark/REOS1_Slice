from contracts.transition_contract import (
	AuthorityMetadata,
	TransitionContract,
)
from runtime.ingress_payload import GovernedIngressPayload
from runtime.transition import derive_transition_id


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
		operation_parameters={},
	)


def make_payload(observation: str) -> GovernedIngressPayload:
	return GovernedIngressPayload(
		payload_id="ING-001",
		raw_observation=observation,
		source_type="user_report",
	)


def test_transition_id_is_deterministic():
	first = derive_transition_id(
		contract=make_contract(),
		payload=make_payload("My system won't shut off."),
	)

	second = derive_transition_id(
		contract=make_contract(),
		payload=make_payload("My system won't shut off."),
	)

	assert first == second
	assert first.startswith("TRN-")


def test_transition_id_changes_when_payload_changes():
	first = derive_transition_id(
		contract=make_contract(),
		payload=make_payload("My system won't shut off."),
	)

	second = derive_transition_id(
		contract=make_contract(),
		payload=make_payload("My thoughts feel heavy."),
	)

	assert first != second
