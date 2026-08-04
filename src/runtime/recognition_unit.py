from dataclasses import dataclass
from typing import Any, Dict

from runtime.ingress_payload import GovernedIngressPayload
from runtime.serializer import canonical_hash


@dataclass(frozen=True)
class RecognitionUnit:
    """
    Immutable unit admitted to REOS recognition.

    It preserves the literal observation and its source payload lineage.
    It performs no basin orientation, interpretation, or recommendation.
    """

    recognition_unit_id: str
    literal_observation: str
    ingress_payload_id: str
    ingress_payload_digest: str
    schema_version: str = "recognition_unit_v1"

    def canonical_data(self) -> Dict[str, Any]:
        return {
            "recognition_unit_id": self.recognition_unit_id,
            "literal_observation": self.literal_observation,
            "ingress_payload_id": self.ingress_payload_id,
            "ingress_payload_digest": self.ingress_payload_digest,
            "schema_version": self.schema_version,
        }

    def digest(self) -> str:
        return canonical_hash(self.canonical_data())


def instantiate_recognition_unit(
    payload: GovernedIngressPayload,
) -> RecognitionUnit:
    """
    Form one deterministic Recognition Unit from one governed payload.

    The identifier is derived from the complete governed payload digest,
    preventing two materially different payloads from sharing an identity.
    """
    payload_digest = payload.digest()

    return RecognitionUnit(
        recognition_unit_id=f"RU-{payload_digest[:12]}",
        literal_observation=payload.raw_observation,
        ingress_payload_id=payload.payload_id,
        ingress_payload_digest=payload_digest,
    )
