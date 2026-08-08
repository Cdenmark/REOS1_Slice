from dataclasses import dataclass
from typing import Tuple

from foundation.canonical import (
    canonical_hash,
    is_valid_canonical_digest,
)


def _require_non_empty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string.")


def _require_canonical_digest(value: str, field_name: str) -> None:
    if not is_valid_canonical_digest(value):
        raise ValueError(
            f"{field_name} must be a canonical 64-character hexadecimal digest."
        )


@dataclass(frozen=True)
class GovernedNounAuthorizationEntry:
    """
    Immutable partial authorization evidence for one artifact representation.

    This noun is envelope-scoped and does not carry authority-context fields.
    """

    artifact_ref: str
    artifact_digest: str
    governed_noun_declaration_id: str
    governed_noun_symbolic_name: str
    verification_report_id: str
    verification_report_digest: str
    authorization_digest: str

    def __post_init__(self) -> None:
        _require_non_empty(self.artifact_ref, "artifact_ref")
        _require_canonical_digest(
            self.artifact_digest,
            "artifact_digest",
        )

        _require_non_empty(
            self.governed_noun_declaration_id,
            "governed_noun_declaration_id",
        )
        _require_non_empty(
            self.governed_noun_symbolic_name,
            "governed_noun_symbolic_name",
        )

        _require_non_empty(
            self.verification_report_id,
            "verification_report_id",
        )
        _require_canonical_digest(
            self.verification_report_digest,
            "verification_report_digest",
        )

        _require_canonical_digest(
            self.authorization_digest,
            "authorization_digest",
        )

    def recompute_authorization_digest(
        self,
        contract_digest: str,
    ) -> str:
        _require_canonical_digest(
            contract_digest,
            "contract_digest",
        )

        material = {
            "artifact_ref": self.artifact_ref,
            "artifact_digest": self.artifact_digest,
            "governed_noun_declaration_id": (
                self.governed_noun_declaration_id
            ),
            "governed_noun_symbolic_name": (
                self.governed_noun_symbolic_name
            ),
            "verification_report_id": self.verification_report_id,
            "verification_report_digest": self.verification_report_digest,
            "authority_context_digest": contract_digest,
        }

        return canonical_hash(material)


@dataclass(frozen=True)
class GovernedNounAuthorizationEnvelope:
    """
    Immutable complete authorization evidence surface.

    This noun carries shared authority context and authorized entry set.
    """

    transition_contract_ref: str
    contract_digest: str
    authorization_entries: Tuple[
        GovernedNounAuthorizationEntry,
        ...,
    ]
    envelope_digest: str

    def __post_init__(self) -> None:
        _require_non_empty(
            self.transition_contract_ref,
            "transition_contract_ref",
        )
        _require_canonical_digest(
            self.contract_digest,
            "contract_digest",
        )
        _require_canonical_digest(
            self.envelope_digest,
            "envelope_digest",
        )

        if not isinstance(self.authorization_entries, tuple):
            raise ValueError(
                "authorization_entries must be a tuple of authorization entries."
            )

        seen_digests: set[str] = set()

        for entry in self.authorization_entries:
            if not isinstance(
                entry,
                GovernedNounAuthorizationEntry,
            ):
                raise ValueError(
                    "authorization_entries must contain only "
                    "GovernedNounAuthorizationEntry values."
                )

            if entry.authorization_digest in seen_digests:
                raise ValueError(
                    "Duplicate authorization_digest values are not allowed "
                    "within one authorization envelope."
                )

            seen_digests.add(entry.authorization_digest)

            recomputed_entry_digest = (
                entry.recompute_authorization_digest(
                    self.contract_digest
                )
            )

            if recomputed_entry_digest != entry.authorization_digest:
                raise ValueError(
                    "Authorization entry digest does not match this "
                    "envelope contract_digest authority context."
                )

        if self.recompute_envelope_digest() != self.envelope_digest:
            raise ValueError(
                "envelope_digest is not valid for the supplied "
                "authority context and authorization entry set."
            )

    def recompute_envelope_digest(self) -> str:
        material = {
            "transition_contract_ref": self.transition_contract_ref,
            "contract_digest": self.contract_digest,
            "authorization_entry_digests": sorted(
                entry.authorization_digest
                for entry in self.authorization_entries
            ),
        }

        return canonical_hash(material)
