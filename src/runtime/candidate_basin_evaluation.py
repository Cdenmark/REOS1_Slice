from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class CandidateBasin:
    """
    One basin presented for constitutional selection.

    This object owns candidate evidence only.
    It does not declare selection or rejection.
    """

    basin_id: str
    evidence_score: float
    evidence_basis: Tuple[str, ...] = ()


@dataclass(frozen=True)
class CandidateBasinEvaluation:
    """
    Immutable pre-decision evaluation surface for REOS-VS002.

    It records the candidates available to the selector.
    It does not select, rank, reject, or orient.
    """

    evaluation_id: str
    recognition_unit_id: str
    candidates: Tuple[CandidateBasin, ...]
    deterministic: bool = True