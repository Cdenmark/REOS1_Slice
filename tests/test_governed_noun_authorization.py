from dataclasses import FrozenInstanceError, fields

import pytest

from foundation.canonical import canonical_hash
import runtime.governed_noun_authorization as authorization_nouns
from runtime.governed_noun_authorization import (
    GovernedNounAuthorizationEntry,
    GovernedNounAuthorizationEnvelope,
)


ENTRY_FIELD_NAMES = (
    "artifact_ref",
    "artifact_digest",
    "governed_noun_declaration_id",
    "governed_noun_symbolic_name",
    "verification_report_id",
    "verification_report_digest",
    "authorization_digest",
)

ENVELOPE_FIELD_NAMES = (
    "transition_contract_ref",
    "contract_digest",
    "authorization_entries",
    "envelope_digest",
)


def _entry_material(
    *,
    artifact_ref: str,
    artifact_digest: str,
    governed_noun_declaration_id: str,
    governed_noun_symbolic_name: str,
    verification_report_id: str,
    verification_report_digest: str,
    contract_digest: str,
) -> dict:
    return {
        "artifact_ref": artifact_ref,
        "artifact_digest": artifact_digest,
        "governed_noun_declaration_id": governed_noun_declaration_id,
        "governed_noun_symbolic_name": governed_noun_symbolic_name,
        "verification_report_id": verification_report_id,
        "verification_report_digest": verification_report_digest,
        "authority_context_digest": contract_digest,
    }


def _derive_entry_digest(**kwargs: str) -> str:
    return canonical_hash(_entry_material(**kwargs))


def _build_entry(
    *,
    contract_digest: str = "c" * 64,
    artifact_ref: str = "SARR-001",
    artifact_digest: str = "a" * 64,
    governed_noun_declaration_id: str = "REOS-004",
    governed_noun_symbolic_name: str = "SeamAwareRecognitionResult",
    verification_report_id: str = "VR3-001",
    verification_report_digest: str = "b" * 64,
) -> GovernedNounAuthorizationEntry:
    authorization_digest = _derive_entry_digest(
        artifact_ref=artifact_ref,
        artifact_digest=artifact_digest,
        governed_noun_declaration_id=governed_noun_declaration_id,
        governed_noun_symbolic_name=governed_noun_symbolic_name,
        verification_report_id=verification_report_id,
        verification_report_digest=verification_report_digest,
        contract_digest=contract_digest,
    )

    return GovernedNounAuthorizationEntry(
        artifact_ref=artifact_ref,
        artifact_digest=artifact_digest,
        governed_noun_declaration_id=governed_noun_declaration_id,
        governed_noun_symbolic_name=governed_noun_symbolic_name,
        verification_report_id=verification_report_id,
        verification_report_digest=verification_report_digest,
        authorization_digest=authorization_digest,
    )


def _envelope_material(
    *,
    transition_contract_ref: str,
    contract_digest: str,
    entry_digests: tuple[str, ...],
) -> dict:
    return {
        "transition_contract_ref": transition_contract_ref,
        "contract_digest": contract_digest,
        "authorization_entry_digests": sorted(entry_digests),
    }


def _derive_envelope_digest(
    *,
    transition_contract_ref: str,
    contract_digest: str,
    entries: tuple[GovernedNounAuthorizationEntry, ...],
) -> str:
    return canonical_hash(
        _envelope_material(
            transition_contract_ref=transition_contract_ref,
            contract_digest=contract_digest,
            entry_digests=tuple(
                entry.authorization_digest for entry in entries
            ),
        )
    )


def _build_envelope(
    *,
    entries: tuple[GovernedNounAuthorizationEntry, ...],
    transition_contract_ref: str = "CONTRACT-REOS-004",
    contract_digest: str = "c" * 64,
) -> GovernedNounAuthorizationEnvelope:
    envelope_digest = _derive_envelope_digest(
        transition_contract_ref=transition_contract_ref,
        contract_digest=contract_digest,
        entries=entries,
    )

    return GovernedNounAuthorizationEnvelope(
        transition_contract_ref=transition_contract_ref,
        contract_digest=contract_digest,
        authorization_entries=entries,
        envelope_digest=envelope_digest,
    )


def test_entry_exact_shape_and_no_prohibited_fields():
    field_names = tuple(
        field.name
        for field in fields(
            GovernedNounAuthorizationEntry
        )
    )

    assert field_names == ENTRY_FIELD_NAMES

    prohibited = {
        "transition_contract_ref",
        "contract_digest",
        "authorization_status",
        "authorization_id",
        "timestamp",
        "actor_id",
        "python_class_identity",
        "module_path",
        "reflection_identity",
        "checkpoint_digest",
        "bundle_id",
        "freeze_line_state",
        "movement_admission",
    }

    assert prohibited.isdisjoint(field_names)


def test_entry_is_frozen_immutable():
    entry = _build_entry()

    with pytest.raises(FrozenInstanceError):
        entry.artifact_ref = "SARR-MUTATED"

    with pytest.raises(FrozenInstanceError):
        entry.authorization_digest = "0" * 64


def test_entry_authorization_digest_is_complete_constitutional_identity():
    entry = _build_entry()

    assert hasattr(entry, "authorization_digest")
    assert not hasattr(entry, "authorization_id")

    expected = _derive_entry_digest(
        artifact_ref=entry.artifact_ref,
        artifact_digest=entry.artifact_digest,
        governed_noun_declaration_id=(
            entry.governed_noun_declaration_id
        ),
        governed_noun_symbolic_name=(
            entry.governed_noun_symbolic_name
        ),
        verification_report_id=entry.verification_report_id,
        verification_report_digest=(
            entry.verification_report_digest
        ),
        contract_digest="c" * 64,
    )

    assert entry.authorization_digest == expected


def test_entry_digest_material_excludes_self_digest_field():
    material = _entry_material(
        artifact_ref="SARR-001",
        artifact_digest="a" * 64,
        governed_noun_declaration_id="REOS-004",
        governed_noun_symbolic_name="SeamAwareRecognitionResult",
        verification_report_id="VR3-001",
        verification_report_digest="b" * 64,
        contract_digest="c" * 64,
    )

    assert "authorization_digest" not in material


def test_entry_digest_deterministic_for_identical_material_and_context():
    first = _build_entry()
    second = _build_entry()

    assert (
        first.authorization_digest
        == second.authorization_digest
    )


def test_entry_digest_changes_when_stable_material_changes():
    baseline = _build_entry().authorization_digest

    assert (
        _build_entry(
            artifact_ref="SARR-ALT"
        ).authorization_digest
        != baseline
    )
    assert (
        _build_entry(
            artifact_digest="d" * 64
        ).authorization_digest
        != baseline
    )
    assert (
        _build_entry(
            governed_noun_declaration_id="REOS-005"
        ).authorization_digest
        != baseline
    )
    assert (
        _build_entry(
            governed_noun_symbolic_name="OrientationResolution"
        ).authorization_digest
        != baseline
    )
    assert (
        _build_entry(
            verification_report_id="VR3-ALT"
        ).authorization_digest
        != baseline
    )
    assert (
        _build_entry(
            verification_report_digest="e" * 64
        ).authorization_digest
        != baseline
    )


def test_entry_digest_changes_when_contract_context_digest_changes():
    first = _build_entry(
        contract_digest="c" * 64
    )
    second = _build_entry(
        contract_digest="f" * 64
    )

    assert (
        first.authorization_digest
        != second.authorization_digest
    )


def test_entry_has_no_time_random_or_history_fields():
    field_names = {
        field.name
        for field in fields(
            GovernedNounAuthorizationEntry
        )
    }

    prohibited = {
        "timestamp",
        "created_at",
        "nonce",
        "random_seed",
        "execution_history",
        "runtime_environment",
    }

    assert prohibited.isdisjoint(field_names)


def test_entry_digest_recomputation_requires_external_contract_digest():
    entry = _build_entry(
        contract_digest="c" * 64
    )

    recomputed = _derive_entry_digest(
        artifact_ref=entry.artifact_ref,
        artifact_digest=entry.artifact_digest,
        governed_noun_declaration_id=(
            entry.governed_noun_declaration_id
        ),
        governed_noun_symbolic_name=(
            entry.governed_noun_symbolic_name
        ),
        verification_report_id=entry.verification_report_id,
        verification_report_digest=(
            entry.verification_report_digest
        ),
        contract_digest="c" * 64,
    )

    assert recomputed == entry.authorization_digest

    wrong_context = _derive_entry_digest(
        artifact_ref=entry.artifact_ref,
        artifact_digest=entry.artifact_digest,
        governed_noun_declaration_id=(
            entry.governed_noun_declaration_id
        ),
        governed_noun_symbolic_name=(
            entry.governed_noun_symbolic_name
        ),
        verification_report_id=entry.verification_report_id,
        verification_report_digest=(
            entry.verification_report_digest
        ),
        contract_digest="9" * 64,
    )

    assert wrong_context != entry.authorization_digest


def test_entry_missing_cni_basis_fields_fail_closed():
    with pytest.raises(ValueError):
        _build_entry(
            governed_noun_declaration_id=""
        )

    with pytest.raises(ValueError):
        _build_entry(
            governed_noun_symbolic_name=""
        )


def test_entry_cni_basis_excludes_runtime_identity_material():
    material = _entry_material(
        artifact_ref="SARR-001",
        artifact_digest="a" * 64,
        governed_noun_declaration_id="REOS-004",
        governed_noun_symbolic_name="SeamAwareRecognitionResult",
        verification_report_id="VR3-001",
        verification_report_digest="b" * 64,
        contract_digest="c" * 64,
    )

    prohibited = {
        "python_class_identity",
        "module_path",
        "reflection_identity",
        "structural_shape",
    }

    assert prohibited.isdisjoint(material.keys())


def test_entry_requires_verification_report_id_and_digest():
    with pytest.raises(ValueError):
        _build_entry(
            verification_report_id=""
        )

    with pytest.raises(ValueError):
        _build_entry(
            verification_report_digest=""
        )


def test_entry_malformed_verification_report_digest_fails_closed():
    with pytest.raises(ValueError):
        _build_entry(
            verification_report_digest="not-a-digest"
        )


def test_report_id_only_binding_is_rejected():
    with pytest.raises(ValueError):
        _build_entry(
            verification_report_digest=""
        )


def test_envelope_exact_shape_and_no_prohibited_fields():
    field_names = tuple(
        field.name
        for field in fields(
            GovernedNounAuthorizationEnvelope
        )
    )

    assert field_names == ENVELOPE_FIELD_NAMES

    prohibited = {
        "authorization_status",
        "required_artifact_count",
        "required_artifact_kinds",
        "checkpoint_canonical_sequence",
        "checkpoint_lineage_closure",
        "checkpoint_digest",
        "bundle_id",
        "freeze_line_identity",
        "movement_admission",
    }

    assert prohibited.isdisjoint(field_names)


def test_envelope_is_frozen_immutable():
    envelope = _build_envelope(entries=())

    with pytest.raises(FrozenInstanceError):
        envelope.transition_contract_ref = "MUTATED"

    with pytest.raises(FrozenInstanceError):
        envelope.envelope_digest = "0" * 64


def test_envelope_digest_is_order_insensitive_for_entry_permutations():
    entry_a = _build_entry(artifact_ref="A")
    entry_b = _build_entry(artifact_ref="B")
    entry_c = _build_entry(artifact_ref="C")

    first = _build_envelope(
        entries=(entry_a, entry_b, entry_c)
    )

    second = _build_envelope(
        entries=(entry_c, entry_a, entry_b)
    )

    assert first.envelope_digest == second.envelope_digest


def test_envelope_rejects_duplicate_entry_authorization_digests():
    entry = _build_entry(artifact_ref="A")

    with pytest.raises(ValueError):
        _build_envelope(
            entries=(entry, entry)
        )


def test_envelope_authority_context_requires_ref_plus_digest():
    with pytest.raises(ValueError):
        _build_envelope(
            entries=(),
            transition_contract_ref="",
        )

    with pytest.raises(ValueError):
        _build_envelope(
            entries=(),
            contract_digest="",
        )


def test_envelope_contract_digest_must_be_canonical_hash_format():
    with pytest.raises(ValueError):
        _build_envelope(
            entries=(),
            contract_digest="bad-digest",
        )


def test_envelope_rejects_entry_digests_from_other_contract_context():
    entry_under_first_context = _build_entry(
        contract_digest="1" * 64,
        artifact_ref="CTX-A",
    )

    with pytest.raises(ValueError):
        _build_envelope(
            entries=(entry_under_first_context,),
            contract_digest="2" * 64,
        )


def test_envelope_digest_is_complete_deterministic_identity():
    entry_a = _build_entry(artifact_ref="A")
    entry_b = _build_entry(artifact_ref="B")

    first = _build_envelope(
        entries=(entry_a, entry_b)
    )
    second = _build_envelope(
        entries=(entry_b, entry_a)
    )

    assert first.envelope_digest == second.envelope_digest


def test_envelope_digest_material_excludes_self_digest():
    material = _envelope_material(
        transition_contract_ref="CONTRACT-REOS-004",
        contract_digest="c" * 64,
        entry_digests=("a" * 64, "b" * 64),
    )

    assert "envelope_digest" not in material


def test_envelope_digest_changes_on_context_or_entry_delta():
    entry_a = _build_entry(
        artifact_ref="A",
        contract_digest="c" * 64,
    )
    entry_b = _build_entry(
        artifact_ref="B",
        contract_digest="c" * 64,
    )

    baseline = _build_envelope(
        entries=(entry_a, entry_b),
        transition_contract_ref="CONTRACT-REOS-004",
        contract_digest="c" * 64,
    ).envelope_digest

    changed_ref = _build_envelope(
        entries=(entry_a, entry_b),
        transition_contract_ref="CONTRACT-ALT",
        contract_digest="c" * 64,
    ).envelope_digest

    changed_context_entry_a = _build_entry(
        artifact_ref="A",
        contract_digest="d" * 64,
    )
    changed_context_entry_b = _build_entry(
        artifact_ref="B",
        contract_digest="d" * 64,
    )

    changed_context_digest = _build_envelope(
        entries=(
            changed_context_entry_a,
            changed_context_entry_b,
        ),
        transition_contract_ref="CONTRACT-REOS-004",
        contract_digest="d" * 64,
    ).envelope_digest

    changed_entries = _build_envelope(
        entries=(entry_a,),
        transition_contract_ref="CONTRACT-REOS-004",
        contract_digest="c" * 64,
    ).envelope_digest

    assert baseline != changed_ref
    assert baseline != changed_context_digest
    assert baseline != changed_entries


def test_bare_entry_is_partial_evidence_and_not_complete_surface():
    entry = _build_entry()
    envelope = _build_envelope(entries=(entry,))

    assert isinstance(
        entry,
        GovernedNounAuthorizationEntry,
    )
    assert isinstance(
        envelope,
        GovernedNounAuthorizationEnvelope,
    )

    assert "authorization_entries" not in {
        field.name
        for field in fields(
            GovernedNounAuthorizationEntry
        )
    }


def test_module_exposes_no_helper_that_elevates_bare_entry_to_complete_authorization():
    prohibited_complete_entry_helpers = {
        "is_complete_authorization_entry",
        "admit_entry_as_complete_authorization",
        "authorize_entry_without_envelope",
    }

    assert prohibited_complete_entry_helpers.isdisjoint(
        authorization_nouns.__dict__
    )


def test_envelope_does_not_claim_binder_or_checkpoint_jurisdiction():
    envelope_fields = {
        field.name
        for field in fields(
            GovernedNounAuthorizationEnvelope
        )
    }

    prohibited = {
        "required_artifact_count",
        "required_artifact_kinds",
        "checkpoint_sequence",
        "checkpoint_lineage",
        "checkpoint_digest",
        "frozen_bundle_identity",
        "movement_admission",
    }

    assert prohibited.isdisjoint(envelope_fields)


def test_noun_layer_does_not_impose_binder_artifact_count_rules():
    zero = _build_envelope(entries=())
    one = _build_envelope(
        entries=(
            _build_entry(artifact_ref="ONE"),
        )
    )
    many = _build_envelope(
        entries=(
            _build_entry(artifact_ref="M1"),
            _build_entry(artifact_ref="M2"),
            _build_entry(artifact_ref="M3"),
            _build_entry(artifact_ref="M4"),
            _build_entry(artifact_ref="M5"),
            _build_entry(artifact_ref="M6"),
        )
    )

    assert isinstance(
        zero,
        GovernedNounAuthorizationEnvelope,
    )
    assert isinstance(
        one,
        GovernedNounAuthorizationEnvelope,
    )
    assert isinstance(
        many,
        GovernedNounAuthorizationEnvelope,
    )
