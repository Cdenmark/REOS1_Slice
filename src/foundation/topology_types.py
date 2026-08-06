from dataclasses import dataclass
from typing import Literal, Tuple


EdgeStatus = Literal[
	"RATIFIED",
	"DEPRECATED",
]

TopologyCheckStatus = Literal[
	"PASS",
	"FAIL",
]

TopologyVerificationState = Literal[
	"VERIFIED",
	"REJECTED",
]


@dataclass(frozen=True)
class DirectedTransitionEdge:
	"""
	One immutable, explicitly directed structural relationship.

	This noun records ratified edge truth only.

	It does not infer reverse edges, perform pathfinding, calculate
	reachability, qualify movement, or execute transitions.
	"""

	edge_id: str
	source_basin: str
	target_basin: str
	relationship_type: str
	authority_ref: str
	status: EdgeStatus


@dataclass(frozen=True)
class TopologyAuthorityMetadata:
	"""
	Immutable authority metadata for a compiled topology artifact.

	This noun identifies the declarations, registry, and compiler
	release that authorized topology compilation.

	It does not compile or verify topology.
	"""

	topology_declaration_id: str
	topology_declaration_version: str
	basin_registry_id: str
	basin_registry_digest: str
	compiler_release: str
	compiler_digest: str


@dataclass(frozen=True)
class TransitionTopology:
	"""
	Immutable compiler-issued directed topology artifact.

	The topology records structural connectivity only.

	It contains no runtime state, evidence scores, momentum values,
	orientation state, movement qualification, or embedded compiler
	behavior.
	"""

	topology_id: str
	topology_version: str
	topology_digest: str
	basin_registry_id: str
	basin_registry_digest: str
	authority: TopologyAuthorityMetadata
	directed_edges: Tuple[DirectedTransitionEdge, ...]
	deterministic: bool = True


@dataclass(frozen=True)
class TopologyProvenance:
	"""
	Immutable compilation-lineage record for TransitionTopology.

	This noun records the authority inputs and compiler identity that
	produced the topology artifact.

	It does not construct, modify, or verify topology.
	"""

	provenance_id: str
	topology_id: str
	topology_digest: str
	declaration_refs: Tuple[str, ...]
	edge_declaration_refs: Tuple[str, ...]
	basin_registry_id: str
	basin_registry_digest: str
	compiler_release: str
	compiler_digest: str
	deterministic: bool = True


@dataclass(frozen=True)
class TopologyVerificationCheck:
	"""
	One independently evaluated topology assertion.
	"""

	check_id: str
	invariant_id: str
	status: TopologyCheckStatus
	message: str


@dataclass(frozen=True)
class TopologyVerificationReport:
	"""
	Immutable output of independent topology verification.

	The report records verification outcomes only.

	It does not construct topology, generate edges, infer reverse
	relationships, or modify the artifact under review.
	"""

	report_id: str
	topology_id: str
	topology_digest: str
	verifier_version: str
	verification_state: TopologyVerificationState
	checks: Tuple[TopologyVerificationCheck, ...]
	deterministic: bool = True