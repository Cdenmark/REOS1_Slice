"""
REOS-VS001 Transition Runtime

This module executes one constitutionally governed
recognition transition.

Current scope:

Ingress Payload
	↓
Recognition Result
	+
Transition Telemetry

Future versions will extend this runtime without
expanding the jurisdiction of this module.
"""

from uuid import uuid4

from contracts.transition_contract import TransitionContract
from runtime.ingress_payload import GovernedIngressPayload
from runtime.serializer import canonical_hash


def new_transition_id() -> str:
	"""
	Allocate a new transition identifier.

	Every governed REOS transition owns one immutable
	transition identity.
	"""

	return f"TRN-{uuid4()}"


def derive_transition_id(
	contract: TransitionContract,
	payload: GovernedIngressPayload,
) -> str:
	"""
	Derive one reproducible transition identity from the complete
	execution mandate and governed ingress payload.

	Identical authority plus identical input produces identical identity.
	"""
	identity_material = {
		"contract_digest": contract.digest(),
		"payload_digest": payload.digest(),
		"transition_id": contract.transition_id,
	}

	return f"TRN-{canonical_hash(identity_material)[:16].upper()}"
