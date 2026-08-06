from dataclasses import asdict
from typing import Set, Tuple

from foundation.canonical import (
	canonical_hash,
	is_valid_canonical_digest,
)
from foundation.topology_types import (
	TopologyProvenance,
	TopologyVerificationCheck,
	TopologyVerificationReport,
	TransitionTopology,
)


class CleanRoomTopologyVerifier:
	"""
	Independent clean-room verifier for REOS topology artifacts.

	Jurisdiction:
	- verify topology and provenance lineage;
	- verify digest representation;
	- verify self-loop prohibition;
	- verify duplicate directed-edge prohibition;
	- verify relationship-type authorization;
	- emit structured verification evidence.

	Prohibited:
	- compiling topology;
	- constructing topology identities;
	- generating edges;
	- inferring reverse edges;
	- repairing artifacts;
	- mutating artifacts;
	- importing runtime or compiler logic.
	"""

	VERSION = "topology-verifier-1.0.0"

	AUTHORIZED_RELATIONSHIP_TYPES = {
		"DIRECT_MOVEMENT_ELIGIBILITY",
	}

	@classmethod
	def verify(
		cls,
		topology: TransitionTopology,
		provenance: TopologyProvenance,
	) -> TopologyVerificationReport:
		checks: list[TopologyVerificationCheck] = []

		digest_valid = is_valid_canonical_digest(
			topology.topology_digest
		)

		checks.append(
			TopologyVerificationCheck(
				check_id="CHK-TOP-001",
				invariant_id="INV-TOP-006",
				status="PASS" if digest_valid else "FAIL",
				message=(
					"Topology digest conforms to canonical digest format."
					if digest_valid
					else "Topology digest does not conform to canonical digest format."
				),
			)
		)

		topology_lineage_valid = (
			topology.topology_id == provenance.topology_id
			and topology.topology_digest
			== provenance.topology_digest
			and topology.basin_registry_id
			== provenance.basin_registry_id
			and topology.basin_registry_digest
			== provenance.basin_registry_digest
			and topology.authority.compiler_release
			== provenance.compiler_release
			and topology.authority.compiler_digest
			== provenance.compiler_digest
		)

		checks.append(
			TopologyVerificationCheck(
				check_id="CHK-TOP-002",
				invariant_id="INV-TOP-001",
				status=(
					"PASS"
					if topology_lineage_valid
					else "FAIL"
				),
				message=(
					"Topology and provenance lineage match."
					if topology_lineage_valid
					else "Topology and provenance lineage do not match."
				),
			)
		)

		self_loop_ids = tuple(
			edge.edge_id
			for edge in topology.directed_edges
			if edge.source_basin == edge.target_basin
		)

		checks.append(
			TopologyVerificationCheck(
				check_id="CHK-TOP-003",
				invariant_id="INV-TOP-002",
				status=(
					"PASS"
					if not self_loop_ids
					else "FAIL"
				),
				message=(
					"No self-directed edges are present."
					if not self_loop_ids
					else (
						"Self-directed edges detected: "
						+ ", ".join(self_loop_ids)
					)
				),
			)
		)

		seen_edge_ids: Set[str] = set()
		duplicate_edge_ids: Set[str] = set()

		seen_directed_relationships: Set[
			Tuple[str, str, str]
		] = set()

		duplicate_relationship_ids: Set[str] = set()

		for edge in topology.directed_edges:
			if edge.edge_id in seen_edge_ids:
				duplicate_edge_ids.add(edge.edge_id)

			seen_edge_ids.add(edge.edge_id)

			relationship_key = (
				edge.source_basin,
				edge.target_basin,
				edge.relationship_type,
			)

			if relationship_key in seen_directed_relationships:
				duplicate_relationship_ids.add(edge.edge_id)

			seen_directed_relationships.add(
				relationship_key
			)

		duplicates_present = bool(
			duplicate_edge_ids
			or duplicate_relationship_ids
		)

		duplicate_messages = sorted(
			duplicate_edge_ids
			| duplicate_relationship_ids
		)

		checks.append(
			TopologyVerificationCheck(
				check_id="CHK-TOP-004",
				invariant_id="INV-TOP-004",
				status=(
					"FAIL"
					if duplicates_present
					else "PASS"
				),
				message=(
					"All directed edges are unique."
					if not duplicates_present
					else (
						"Duplicate edges detected: "
						+ ", ".join(duplicate_messages)
					)
				),
			)
		)

		invalid_relationship_edge_ids = tuple(
			edge.edge_id
			for edge in topology.directed_edges
			if edge.relationship_type
			not in cls.AUTHORIZED_RELATIONSHIP_TYPES
		)

		checks.append(
			TopologyVerificationCheck(
				check_id="CHK-TOP-005",
				invariant_id="INV-TOP-005",
				status=(
					"PASS"
					if not invalid_relationship_edge_ids
					else "FAIL"
				),
				message=(
					"All relationship types are authorized."
					if not invalid_relationship_edge_ids
					else (
						"Unauthorized relationship types detected on edges: "
						+ ", ".join(
							invalid_relationship_edge_ids
						)
					)
				),
			)
		)

		invalid_status_edge_ids = tuple(
			edge.edge_id
			for edge in topology.directed_edges
			if edge.status
			not in {
				"RATIFIED",
				"DEPRECATED",
			}
		)

		checks.append(
			TopologyVerificationCheck(
				check_id="CHK-TOP-006",
				invariant_id="INV-TOP-005",
				status=(
					"PASS"
					if not invalid_status_edge_ids
					else "FAIL"
				),
				message=(
					"All edge statuses are valid."
					if not invalid_status_edge_ids
					else (
						"Invalid edge statuses detected on edges: "
						+ ", ".join(
							invalid_status_edge_ids
						)
					)
				),
			)
		)

		verification_state = (
			"VERIFIED"
			if all(
				check.status == "PASS"
				for check in checks
			)
			else "REJECTED"
		)

		report_material = {
			"topology_id": topology.topology_id,
			"topology_digest": topology.topology_digest,
			"verifier_version": cls.VERSION,
			"verification_state": verification_state,
			"checks": [
				asdict(check)
				for check in checks
			],
		}

		report_id = (
			"TVR-"
			+ canonical_hash(report_material)[:16].upper()
		)

		return TopologyVerificationReport(
			report_id=report_id,
			topology_id=topology.topology_id,
			topology_digest=topology.topology_digest,
			verifier_version=cls.VERSION,
			verification_state=verification_state,
			checks=tuple(checks),
		)