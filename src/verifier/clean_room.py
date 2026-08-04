import hashlib
import json
from dataclasses import asdict, is_dataclass
from typing import Any, Dict


class VerificationError(Exception):
    """Raised when emitted artifacts cannot be independently reproduced."""


def _canonical_json_bytes(data: Any) -> bytes:
    """
    Independent deterministic serializer.

    This implementation intentionally does not import runtime.serializer.
    """
    serialized = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return serialized.encode("utf-8")


def _canonical_hash(data: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(data)).hexdigest()


def _to_dict(value: Any) -> Dict[str, Any]:
    if is_dataclass(value):
        return asdict(value)

    if isinstance(value, dict):
        return value

    raise TypeError("Verifier accepts dataclass instances or dictionaries.")


def _contract_digest(contract: Dict[str, Any]) -> str:
    authority = contract["authority"]

    return _canonical_hash(
        {
            "contract_id": contract["contract_id"],
            "transition_id": contract["transition_id"],
            "authority": {
                "declaration_id": authority["declaration_id"],
                "declaration_hash": authority["declaration_hash"],
                "compiler_release": authority["compiler_release"],
                "compiler_digest": authority["compiler_digest"],
                "generated_at": authority["generated_at"],
            },
            "constitution_version": contract["constitution_version"],
            "contract_version": contract["contract_version"],
            "allowed_operations": sorted(
                contract["allowed_operations"]
            ),
            "permitted_exports": sorted(
                contract["permitted_exports"]
            ),
            "prohibited_exports": sorted(
                contract["prohibited_exports"]
            ),
        }
    )


def verify_reos001(
    contract: Any,
    payload: Any,
    result: Any,
    telemetry: Any,
) -> bool:
    """
    Independently reconstruct and verify one REOS-001 execution.

    This verifier does not import or call:
    - runtime.serializer
    - runtime.transition
    - runtime.orientation
    - runtime.recognition_unit
    - runtime.reos001
    """
    contract_data = _to_dict(contract)
    payload_data = _to_dict(payload)
    result_data = _to_dict(result)
    telemetry_data = _to_dict(telemetry)

    payload_digest = _canonical_hash(payload_data)
    contract_digest = _contract_digest(contract_data)

    expected_transition_id = (
        "TRN-"
        + _canonical_hash(
            {
                "contract_digest": contract_digest,
                "payload_digest": payload_digest,
                "transition_id": contract_data["transition_id"],
            }
        )[:16].upper()
    )

    expected_recognition_unit_id = (
        f"RU-{payload_digest[:12]}"
    )

    observation = payload_data["raw_observation"]

    if "shut off" not in observation.casefold():
        raise VerificationError(
            "Independent orientation reconstruction failed."
        )

    expected_primary_basin = "REC-002"

    expected_recognition_id = (
        "RR-"
        + _canonical_hash(
            {
                "transition_id": expected_transition_id,
                "recognition_unit_id": (
                    expected_recognition_unit_id
                ),
                "primary_basin": expected_primary_basin,
            }
        )[:16].upper()
    )

    expected_operation_trace = [
        {
            "sequence": 1,
            "operation_name": "ingress_hash",
        },
        {
            "sequence": 2,
            "operation_name": "instantiate_recognition_unit",
        },
        {
            "sequence": 3,
            "operation_name": "determine_primary_basin",
        },
    ]

    checks = {
        "transition_id": (
            telemetry_data["transition_id"]
            == expected_transition_id
        ),
        "trace_id": (
            telemetry_data["trace_id"]
            == f"TRACE-{expected_transition_id}"
        ),
        "declaration_hash": (
            telemetry_data["declaration_hash"]
            == contract_data["authority"]["declaration_hash"]
        ),
        "operation_trace": (
            telemetry_data["operation_trace"]
            == expected_operation_trace
        ),
        "telemetry_basin": (
            telemetry_data["selected_basin"]
            == expected_primary_basin
        ),
        "lineage": (
            telemetry_data["lineage"]["parent_artifacts"]
            == [payload_digest, contract_digest]
        ),
        "recognition_id": (
            result_data["recognition_id"]
            == expected_recognition_id
        ),
        "recognition_unit_id": (
            result_data["recognition_unit_id"]
            == expected_recognition_unit_id
        ),
        "result_basin": (
            result_data["orientation"]["primary_basin"]
            == expected_primary_basin
        ),
        "resolution_state": (
            result_data["resolution_state"] == "oriented"
        ),
        "payload_lineage": (
            result_data["provenance"]["ingress_payload_id"]
            == payload_data["payload_id"]
        ),
        "contract_lineage": (
            result_data["provenance"]["contract_version"]
            == contract_data["contract_version"]
        ),
    }

    failed_checks = [
        name
        for name, passed in checks.items()
        if not passed
    ]

    if failed_checks:
        raise VerificationError(
            "Independent verification failed: "
            + ", ".join(failed_checks)
        )

    return True
