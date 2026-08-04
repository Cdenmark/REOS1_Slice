from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class OperationTraceEntry:
	"""One ordered runtime operation executed under contract authority."""

	sequence: int
	operation_name: str


@dataclass(frozen=True)
class RejectedBasin:
	"""A candidate basin excluded during orientation."""

	basin_id: str
	rejection_reason: str


@dataclass(frozen=True)
class ArtifactLineage:
	"""Provenance owned by the telemetry artifact."""

	parent_artifacts: List[str]
	produced_by: str
	certified_by: str


@dataclass(frozen=True)
class TransitionTelemetry:
	"""
	Immutable explanatory record for one REOS transition.

	This object answers only:

	    What happened during execution?

	It cannot modify or reinterpret the RecognitionResult.
	"""

	trace_id: str

	transition_id: str

	declaration_hash: str

	constitution_version: str

	compiler_version: str

	contract_version: str

	runtime_version: str

	operation_trace: List[OperationTraceEntry]

	candidate_basins: List[str]

	selected_basin: str

	rejected_basins: List[RejectedBasin]

	evaluated_seams: List[str] = field(default_factory=list)

	termination_reason: str = ""

	lineage: Optional[ArtifactLineage] = None
