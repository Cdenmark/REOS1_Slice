from dataclasses import dataclass
from typing import Any, Dict

from runtime.serializer import canonical_hash


@dataclass(frozen=True)
class GovernedIngressPayload:
    """
    Immutable input admitted to REOS-VS001.

    This object preserves the literal human observation.
    It performs no recognition, interpretation, or orientation.
    """

    payload_id: str
    raw_observation: str
    source_type: str
    schema_version: str = "ingress_payload_v1"

    def canonical_data(self) -> Dict[str, Any]:
        return {
            "payload_id": self.payload_id,
            "raw_observation": self.raw_observation,
            "source_type": self.source_type,
            "schema_version": self.schema_version,
        }

    def digest(self) -> str:
        """Return the deterministic identity digest of this payload."""
        return canonical_hash(self.canonical_data())
