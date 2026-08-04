from dataclasses import dataclass, field
from typing import List, Literal, Optional


ResolutionState = Literal[
	"oriented",
	"clarification_required",
	"unresolved",
]


@dataclass(frozen=True)
class BasinOrientation:
	"""
	Constitutionally owned orientation.

	Exactly one primary basin is permitted
	for REOS Vertical Slice 001.
	"""

	primary_basin: str
	active_seam: Optional[str] = None
	directional_momentum: Optional[str] = None


@dataclass(frozen=True)
class Provenance:
	"""
	Runtime lineage.

	Every emitted object must be traceable
	back to its governed ingress payload.
	"""

	ingress_payload_id: str
	contract_version: str


@dataclass(frozen=True)
class RecognitionResult:
	"""
	Canonical operational output of REOS-VS001.

	This object answers ONLY:

		What did REOS recognize?

	It never explains how.
	"""

	recognition_id: str

	recognition_unit_id: str

	orientation: BasinOrientation

	resolution_state: ResolutionState

	residual_observations: List[str] = field(default_factory=list)

	provenance: Provenance = field(default=None)
