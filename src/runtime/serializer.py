import hashlib
import json
from typing import Any


def canonical_json_bytes(data: Any) -> bytes:
    """
    Produce deterministic UTF-8 JSON bytes for REOS-VS001.

    This is intentionally Python-native canonical serialization:
    - object keys sorted
    - compact separators
    - UTF-8 output
    - non-ASCII characters preserved

    Production multi-language deployment should replace this module
    with a strict RFC 8785 JSON Canonicalization Scheme implementation.
    """
    serialized = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return serialized.encode("utf-8")


def canonical_hash(data: Any) -> str:
    """Return the SHA-256 hex digest of deterministic JSON bytes."""
    return hashlib.sha256(canonical_json_bytes(data)).hexdigest()
