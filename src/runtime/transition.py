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


def new_transition_id() -> str:
	"""
	Allocate a new transition identifier.

	Every governed REOS transition owns one immutable
	transition identity.
	"""

	return f"TRN-{uuid4()}"
