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


def is_valid_canonical_digest(value: object) -> bool:
	"""
	Return whether value conforms to the repository's canonical
	hexadecimal digest representation.
	"""
	if not isinstance(value, str):
		return False

	if len(value) != 64:
		return False

	try:
		int(value, 16)
	except ValueError:
		return False

	return True