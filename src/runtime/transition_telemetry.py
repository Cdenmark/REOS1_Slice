from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class RuleTraceEntry:
	"""
	One compiler-certified rule execution.
	"""

	sequence: int
	rule_id: str


@dataclass(frozen=True)
class RejectedBasin:
	"""
	Candidate basin eliminated during orientation.
	"""

	basin_id: str
	rejection_reason: str


@dataclass(frozen=True)
class ArtifactLineage:
	"""
	Provenance owned by this telemetry artifact.
	"""

	parent_artifacts: List[str]

	compiler_version: str

	verifier_version: str


@dataclass(frozen=True)
class TransitionTelemetry:
	"""
	Immutable execution evidence.

	This object explains execution.

	It NEVER changes execution.
	"""

	trace_id: str

	transition_id: str

	declaration_hash: str

	constitution_version: str

	compiler_version: str

	contract_version: str

	runtime_version: str

	candidate_basins: List[str]

	selected_basin: str

	rejected_basins: List[RejectedBasin]

	rule_trace: List[RuleTraceEntry]

	evaluated_seams: List[str] = field(default_factory=list)

	termination_reason: str = ""

	lineage: Optional[ArtifactLineage] = None
