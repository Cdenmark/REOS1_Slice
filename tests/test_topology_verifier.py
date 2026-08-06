from dataclasses import replace

from foundation.topology_types import (
	DirectedTransitionEdge,
	TopologyAuthorityMetadata,
	TopologyProvenance,
	TransitionTopology,
)
from verifier.topology_verifier import (
	CleanRoomTopologyVerifier,
)


def make_authority() -> TopologyAuthorityMetadata:
	return TopologyAuthorityMetadata(
		topology_declaration_id="REOS-TOPOLOGY-001",
		topology_declaration_version="1.0.0",
		basin_registry_id="BR-REOS-001",
		basin_registry_digest="a" * 64,
		compiler_release="topology-compiler-1.0.0",
		compiler_digest="b" * 64,
	)


def make_edges() -> tuple[DirectedTransitionEdge, ...]:
	return (
		DirectedTransitionEdge(
			edge_id="EDGE-001",
			source_basin="REC-002",
			target_basin="REC-005",
			relationship_type=(
				"DIRECT_MOVEMENT_ELIGIBILITY"
			),
			authority_ref="REOS-TOPOLOGY-001",
			status="RATIFIED",
		),
		DirectedTransitionEdge(
			edge_id="EDGE-002",
			source_basin="REC-002",
			target_basin="REC-007",
			relationship_type=(
				"DIRECT_MOVEMENT_ELIGIBILITY"
			),
			authority_ref="REOS-TOPOLOGY-001",
			status="RATIFIED",
		),
	)


def make_topology(
	*,
	edges: tuple[DirectedTransitionEdge, ...] | None = None,
	topology_digest: str = "c" * 64,
) -> TransitionTopology:
	return TransitionTopology(
		topology_id="TT-REOS-001",
		topology_version="1.0.0",
		topology_digest=topology_digest,
		basin_registry_id="BR-REOS-001",
		basin_registry_digest="a" * 64,
		authority=make_authority(),
		directed_edges=(
			make_edges()
			if edges is None
			else edges
		),
	)


def make_provenance() -> TopologyProvenance:
	return TopologyProvenance(
		provenance_id="TPROV-001",
		topology_id="TT-REOS-001",
		topology_digest="c" * 64,
		declaration_refs=(
			"REOS-TOPOLOGY-001",
		),
		edge_declaration_refs=(
			"EDGE-DECL-001",
			"EDGE-DECL-002",
		),
		basin_registry_id="BR-REOS-001",
		basin_registry_digest="a" * 64,
		compiler_release="topology-compiler-1.0.0",
		compiler_digest="b" * 64,
	)


def find_check(report, check_id: str):
	return next(
		check
		for check in report.checks
		if check.check_id == check_id
	)


def test_valid_topology_is_verified():
	report = CleanRoomTopologyVerifier.verify(
		topology=make_topology(),
		provenance=make_provenance(),
	)

	assert report.verification_state == "VERIFIED"
	assert all(
		check.status == "PASS"
		for check in report.checks
	)


def test_malformed_digest_is_rejected():
	report = CleanRoomTopologyVerifier.verify(
		topology=make_topology(
			topology_digest="not-a-digest"
		),
		provenance=replace(
			make_provenance(),
			topology_digest="not-a-digest",
		),
	)

	assert report.verification_state == "REJECTED"
	assert find_check(
		report,
		"CHK-TOP-001",
	).status == "FAIL"


def test_provenance_mismatch_is_rejected():
	report = CleanRoomTopologyVerifier.verify(
		topology=make_topology(),
		provenance=replace(
			make_provenance(),
			topology_id="TT-DIFFERENT",
		),
	)

	assert report.verification_state == "REJECTED"
	assert find_check(
		report,
		"CHK-TOP-002",
	).status == "FAIL"


def test_self_directed_edge_is_rejected():
	self_loop = DirectedTransitionEdge(
		edge_id="EDGE-LOOP",
		source_basin="REC-002",
		target_basin="REC-002",
		relationship_type=(
			"DIRECT_MOVEMENT_ELIGIBILITY"
		),
		authority_ref="REOS-TOPOLOGY-001",
		status="RATIFIED",
	)

	report = CleanRoomTopologyVerifier.verify(
		topology=make_topology(
			edges=(self_loop,)
		),
		provenance=make_provenance(),
	)

	assert report.verification_state == "REJECTED"
	assert find_check(
		report,
		"CHK-TOP-003",
	).status == "FAIL"


def test_duplicate_directed_edge_is_rejected():
	first = make_edges()[0]

	duplicate = replace(
		first,
		edge_id="EDGE-DUPLICATE",
	)

	report = CleanRoomTopologyVerifier.verify(
		topology=make_topology(
			edges=(first, duplicate)
		),
		provenance=make_provenance(),
	)

	assert report.verification_state == "REJECTED"
	assert find_check(
		report,
		"CHK-TOP-004",
	).status == "FAIL"


def test_reverse_edge_is_distinct_and_permitted():
	forward = DirectedTransitionEdge(
		edge_id="EDGE-001",
		source_basin="REC-002",
		target_basin="REC-005",
		relationship_type=(
			"DIRECT_MOVEMENT_ELIGIBILITY"
		),
		authority_ref="REOS-TOPOLOGY-001",
		status="RATIFIED",
	)

	reverse = DirectedTransitionEdge(
		edge_id="EDGE-002",
		source_basin="REC-005",
		target_basin="REC-002",
		relationship_type=(
			"DIRECT_MOVEMENT_ELIGIBILITY"
		),
		authority_ref="REOS-TOPOLOGY-001",
		status="RATIFIED",
	)

	report = CleanRoomTopologyVerifier.verify(
		topology=make_topology(
			edges=(forward, reverse)
		),
		provenance=make_provenance(),
	)

	assert find_check(
		report,
		"CHK-TOP-004",
	).status == "PASS"


def test_unknown_relationship_type_is_rejected():
	invalid_edge = replace(
		make_edges()[0],
		relationship_type="UNKNOWN_RELATIONSHIP",
	)

	report = CleanRoomTopologyVerifier.verify(
		topology=make_topology(
			edges=(invalid_edge,)
		),
		provenance=make_provenance(),
	)

	assert report.verification_state == "REJECTED"
	assert find_check(
		report,
		"CHK-TOP-005",
	).status == "FAIL"


def test_repeated_verification_is_deterministic():
	topology = make_topology()
	provenance = make_provenance()

	first = CleanRoomTopologyVerifier.verify(
		topology=topology,
		provenance=provenance,
	)

	second = CleanRoomTopologyVerifier.verify(
		topology=topology,
		provenance=provenance,
	)

	assert first == second
	assert first.report_id == second.report_id