"""Recognition checkpoint binder for REOS-004.

This module owns checkpoint membership, exact-set, lineage, digest, and
FrozenRecognitionBundle construction once successful authorization evidence has
already been supplied upstream.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, NoReturn

from contracts.transition_contract import TransitionContract
from foundation.canonical import canonical_hash, is_valid_canonical_digest
from runtime.basin_selector import BasinSelection
from runtime.candidate_basin_evaluation import CandidateBasinEvaluation
from runtime.governed_noun_authorization import (
    GovernedNounAuthorizationEntry,
    GovernedNounAuthorizationEnvelope,
)
from runtime.movement_exceptions import RecognitionCheckpointBindingError
from runtime.movement_types import (
    FrozenRecognitionBundle,
    RecognitionArtifactBinding,
)
from runtime.orientation_resolution import OrientationResolution
from runtime.seam_activation import SeamActivationCondition
from runtime.seam_aware_recognition_result import SeamAwareRecognitionResult


AUTHORIZATION_ENVELOPE_INVALID = (
    "RECOGNITION_CHECKPOINT_AUTHORIZATION_ENVELOPE_INVALID"
)
ARTIFACT_UNAUTHORIZED = (
    "RECOGNITION_CHECKPOINT_ARTIFACT_UNAUTHORIZED"
)

_CHECKPOINT_SEQUENCE = (
    (
        "candidate_evaluation",
        "CANDIDATE_BASIN_EVALUATION",
        CandidateBasinEvaluation,
        "evaluation_id",
        "CandidateBasinEvaluation",
    ),
    (
        "basin_selection",
        "BASIN_SELECTION",
        BasinSelection,
        "selection_id",
        "BasinSelection",
    ),
    (
        "seam_activation_condition",
        "SEAM_ACTIVATION_CONDITION",
        SeamActivationCondition,
        "condition_id",
        "SeamActivationCondition",
    ),
    (
        "orientation_resolution",
        "ORIENTATION_RESOLUTION",
        OrientationResolution,
        "resolution_id",
        "OrientationResolution",
    ),
    (
        "seam_aware_recognition_result",
        "SEAM_AWARE_RECOGNITION_RESULT",
        SeamAwareRecognitionResult,
        "result_id",
        "SeamAwareRecognitionResult",
    ),
)


def _raise_binding_error(reason_code: str, message: str) -> NoReturn:
    error = RecognitionCheckpointBindingError.__new__(
        RecognitionCheckpointBindingError
    )
    Exception.__init__(error, f"[{reason_code}] {message}")
    error.reason_code = reason_code
    error.message = message
    raise error


def _require_canonical_digest(value: Any, reason_code: str, message: str) -> str:
    if not is_valid_canonical_digest(value):
        _raise_binding_error(reason_code, message)

    return value


def _artifact_digest(artifact: Any) -> str:
    return canonical_hash(asdict(artifact))


def _artifact_id(artifact: Any, ref_attr: str) -> str:
    value = getattr(artifact, ref_attr, None)

    if not isinstance(value, str) or not value:
        _raise_binding_error(
            "ARTIFACT_TYPE_MISMATCH",
            f"{artifact.__class__.__name__} is missing a valid {ref_attr}.",
        )

    return value


def _expected_authorization_symbol(kind_name: str) -> str:
    return kind_name


def _find_matching_authorization_entry(
    envelope: GovernedNounAuthorizationEnvelope,
    *,
    artifact_ref: str,
    artifact_digest: str,
    governed_noun_declaration_id: str,
    governed_noun_symbolic_name: str,
) -> GovernedNounAuthorizationEntry | None:
    for entry in envelope.authorization_entries:
        if not isinstance(entry, GovernedNounAuthorizationEntry):
            continue

        if (
            entry.artifact_ref == artifact_ref
            and entry.artifact_digest == artifact_digest
            and entry.governed_noun_declaration_id
            == governed_noun_declaration_id
            and entry.governed_noun_symbolic_name
            == governed_noun_symbolic_name
        ):
            return entry

    return None


def _validate_authorization_envelope(
    envelope: Any,
    contract: TransitionContract,
) -> GovernedNounAuthorizationEnvelope:
    if not isinstance(envelope, GovernedNounAuthorizationEnvelope):
        _raise_binding_error(
            AUTHORIZATION_ENVELOPE_INVALID,
            "A GovernedNounAuthorizationEnvelope is required.",
        )

    if not isinstance(contract, TransitionContract):
        _raise_binding_error(
            AUTHORIZATION_ENVELOPE_INVALID,
            "A TransitionContract is required.",
        )

    if "bind_recognition_checkpoint" not in contract.allowed_operations:
        _raise_binding_error(
            AUTHORIZATION_ENVELOPE_INVALID,
            "The active TransitionContract does not authorize bind_recognition_checkpoint.",
        )

    contract_digest = contract.digest()

    if envelope.transition_contract_ref != contract.contract_id:
        _raise_binding_error(
            AUTHORIZATION_ENVELOPE_INVALID,
            "Authorization envelope transition_contract_ref does not match the active TransitionContract.",
        )

    if envelope.contract_digest != contract_digest:
        _raise_binding_error(
            AUTHORIZATION_ENVELOPE_INVALID,
            "Authorization envelope contract_digest does not match the active TransitionContract.",
        )

    if envelope.recompute_envelope_digest() != envelope.envelope_digest:
        _raise_binding_error(
            AUTHORIZATION_ENVELOPE_INVALID,
            "Authorization envelope digest is not valid for the supplied evidence.",
        )

    _require_canonical_digest(
        envelope.envelope_digest,
        AUTHORIZATION_ENVELOPE_INVALID,
        "Authorization envelope digest is malformed.",
    )

    return envelope


def _build_frozen_bundle(
    *,
    recognition_unit_id: str,
    artifact_bindings: tuple[RecognitionArtifactBinding, ...],
) -> FrozenRecognitionBundle:
    checkpoint_material = {
        "recognition_unit_id": recognition_unit_id,
        "candidate_evaluation_ref": artifact_bindings[0].artifact_id,
        "basin_selection_ref": artifact_bindings[1].artifact_id,
        "seam_activation_condition_ref": artifact_bindings[2].artifact_id,
        "orientation_resolution_ref": artifact_bindings[3].artifact_id,
        "seam_aware_result_ref": artifact_bindings[4].artifact_id,
        "artifact_bindings": [asdict(binding) for binding in artifact_bindings],
        "deterministic": True,
    }

    recognition_checkpoint_digest = canonical_hash(checkpoint_material)

    bundle_material = {
        "material_type": "FROZEN_RECOGNITION_BUNDLE_ID",
        "recognition_checkpoint_digest": recognition_checkpoint_digest,
    }

    bundle_id = (
        "FRB-"
        + canonical_hash(bundle_material)[:16].upper()
    )

    return FrozenRecognitionBundle(
        bundle_id=bundle_id,
        recognition_unit_id=recognition_unit_id,
        candidate_evaluation_ref=artifact_bindings[0].artifact_id,
        basin_selection_ref=artifact_bindings[1].artifact_id,
        seam_activation_condition_ref=artifact_bindings[2].artifact_id,
        orientation_resolution_ref=artifact_bindings[3].artifact_id,
        seam_aware_result_ref=artifact_bindings[4].artifact_id,
        artifact_bindings=artifact_bindings,
        recognition_checkpoint_digest=recognition_checkpoint_digest,
        deterministic=True,
    )


class RecognitionCheckpointBinder:
    """Stateless binder for REOS-004 recognition checkpoints."""

    def bind_recognition_checkpoint(
        self,
        *,
        candidate_evaluation: Any = None,
        basin_selection: Any = None,
        seam_activation_condition: Any = None,
        orientation_resolution: Any = None,
        seam_aware_recognition_result: Any = None,
        authorization_envelope: Any = None,
        contract: Any = None,
    ) -> FrozenRecognitionBundle:
        envelope = _validate_authorization_envelope(
            authorization_envelope,
            contract,
        )

        requested_artifacts = (
            candidate_evaluation,
            basin_selection,
            seam_activation_condition,
            orientation_resolution,
            seam_aware_recognition_result,
        )

        # Pre-stage 0B: evidence binding. Only supplied artifacts participate
        # in coverage checks; missing artifacts are handled by Stage 1.
        for artifact, spec in zip(requested_artifacts, _CHECKPOINT_SEQUENCE):
            field_name, kind_name, expected_type, ref_attr, noun_name = spec

            if artifact is None:
                continue

            if not isinstance(artifact, expected_type):
                _raise_binding_error(
                    "ARTIFACT_TYPE_MISMATCH",
                    f"{field_name} must be a {expected_type.__name__}.",
                )

            artifact_id = _artifact_id(artifact, ref_attr)
            artifact_digest = _artifact_digest(artifact)
            matching_entry = _find_matching_authorization_entry(
                envelope,
                artifact_ref=artifact_id,
                artifact_digest=artifact_digest,
                governed_noun_declaration_id="REOS-004",
                governed_noun_symbolic_name=noun_name,
            )

            if matching_entry is None:
                _raise_binding_error(
                    ARTIFACT_UNAUTHORIZED,
                    f"{field_name} is not covered by a matching authorization entry.",
                )

        for artifact, spec in zip(requested_artifacts, _CHECKPOINT_SEQUENCE):
            field_name, kind_name, expected_type, ref_attr, noun_name = spec

            if artifact is None:
                _raise_binding_error(
                    "MISSING_REQUIRED_ARTIFACT",
                    f"{field_name} is required for recognition checkpoint binding.",
                )

            if not isinstance(artifact, expected_type):
                _raise_binding_error(
                    "ARTIFACT_TYPE_MISMATCH",
                    f"{field_name} must be a {expected_type.__name__}.",
                )

        candidate_evaluation = candidate_evaluation
        basin_selection = basin_selection
        seam_activation_condition = seam_activation_condition
        orientation_resolution = orientation_resolution
        seam_aware_recognition_result = seam_aware_recognition_result

        candidate_unit_id = candidate_evaluation.recognition_unit_id

        if basin_selection.evaluation_id != candidate_evaluation.evaluation_id:
            _raise_binding_error(
                "EVALUATION_LINEAGE_MISMATCH",
                "BasinSelection does not reference the supplied CandidateBasinEvaluation.",
            )

        if seam_activation_condition.evaluation_id != candidate_evaluation.evaluation_id:
            _raise_binding_error(
                "EVALUATION_LINEAGE_MISMATCH",
                "SeamActivationCondition does not reference the supplied CandidateBasinEvaluation.",
            )

        if candidate_evaluation.recognition_unit_id != seam_activation_condition.recognition_unit_id:
            _raise_binding_error(
                "RECOGNITION_UNIT_MISMATCH",
                "CandidateBasinEvaluation and SeamActivationCondition recognition unit identities do not match.",
            )

        if basin_selection.primary_basin != seam_activation_condition.participating_basins[0].basin_id and basin_selection.primary_basin != seam_activation_condition.participating_basins[1].basin_id:
            _raise_binding_error(
                "SELECTION_LINEAGE_MISMATCH",
                "Selected primary basin is absent from the seam participants.",
            )

        if orientation_resolution.selection_id != basin_selection.selection_id:
            _raise_binding_error(
                "SELECTION_LINEAGE_MISMATCH",
                "OrientationResolution does not reference the supplied BasinSelection.",
            )

        if orientation_resolution.seam_condition_id != seam_activation_condition.condition_id:
            _raise_binding_error(
                "SEAM_LINEAGE_MISMATCH",
                "OrientationResolution does not reference the supplied SeamActivationCondition.",
            )

        if seam_aware_recognition_result.orientation_resolution_id != orientation_resolution.resolution_id:
            _raise_binding_error(
                "ORIENTATION_LINEAGE_MISMATCH",
                "SeamAwareRecognitionResult does not reference the supplied OrientationResolution.",
            )

        if seam_aware_recognition_result.base_result.recognition_unit_id != candidate_unit_id:
            _raise_binding_error(
                "BASE_RESULT_RECOGNITION_UNIT_MISMATCH",
                "SeamAwareRecognitionResult base result does not preserve the recognition unit identity.",
            )

        if seam_aware_recognition_result.base_result.orientation.primary_basin != basin_selection.primary_basin:
            _raise_binding_error(
                "BASE_RESULT_SELECTION_OUTCOME_MISMATCH",
                "SeamAwareRecognitionResult base result does not preserve the selected primary basin.",
            )

        artifact_bindings = tuple(
            RecognitionArtifactBinding(
                artifact_kind=kind_name,
                artifact_id=_artifact_id(artifact, ref_attr),
                artifact_digest=_artifact_digest(artifact),
            )
            for artifact, (_, kind_name, _, ref_attr, _) in zip(
                requested_artifacts,
                _CHECKPOINT_SEQUENCE,
            )
            if artifact is not None
        )

        required_kinds = [spec[1] for spec in _CHECKPOINT_SEQUENCE]
        actual_kinds = [binding.artifact_kind for binding in artifact_bindings]

        if len(actual_kinds) != 5:
            _raise_binding_error(
                "ARTIFACT_SET_MISMATCH",
                "Recognition checkpoint requires exactly five artifact bindings.",
            )

        if len(set(actual_kinds)) != len(actual_kinds):
            _raise_binding_error(
                "DUPLICATE_ARTIFACT_KIND",
                "Recognition checkpoint contains duplicate artifact kinds.",
            )

        artifact_ids = [binding.artifact_id for binding in artifact_bindings]

        if len(set(artifact_ids)) != len(artifact_ids):
            _raise_binding_error(
                "DUPLICATE_ARTIFACT_ID",
                "Recognition checkpoint contains duplicate artifact identities.",
            )

        expected_kind_sequence = [spec[1] for spec in _CHECKPOINT_SEQUENCE]

        if actual_kinds != expected_kind_sequence:
            _raise_binding_error(
                "CANONICAL_SEQUENCE_VIOLATION",
                "Recognition checkpoint artifact bindings do not follow the declared canonical sequence.",
            )

        checkpoint_digest_material = {
            "recognition_unit_id": candidate_unit_id,
            "candidate_evaluation_ref": candidate_evaluation.evaluation_id,
            "basin_selection_ref": basin_selection.selection_id,
            "seam_activation_condition_ref": seam_activation_condition.condition_id,
            "orientation_resolution_ref": orientation_resolution.resolution_id,
            "seam_aware_result_ref": seam_aware_recognition_result.result_id,
            "artifact_bindings": [asdict(binding) for binding in artifact_bindings],
            "deterministic": True,
        }

        for binding in artifact_bindings:
            if not is_valid_canonical_digest(binding.artifact_digest):
                _raise_binding_error(
                    "DIGEST_CONSTRUCTION_FAILURE",
                    "Artifact digest is not canonical.",
                )

        recognition_checkpoint_digest = canonical_hash(checkpoint_digest_material)

        bundle_material = {
            "material_type": "FROZEN_RECOGNITION_BUNDLE_ID",
            "recognition_checkpoint_digest": recognition_checkpoint_digest,
        }

        bundle_id = (
            "FRB-"
            + canonical_hash(bundle_material)[:16].upper()
        )

        return FrozenRecognitionBundle(
            bundle_id=bundle_id,
            recognition_unit_id=candidate_unit_id,
            candidate_evaluation_ref=candidate_evaluation.evaluation_id,
            basin_selection_ref=basin_selection.selection_id,
            seam_activation_condition_ref=seam_activation_condition.condition_id,
            orientation_resolution_ref=orientation_resolution.resolution_id,
            seam_aware_result_ref=seam_aware_recognition_result.result_id,
            artifact_bindings=artifact_bindings,
            recognition_checkpoint_digest=recognition_checkpoint_digest,
            deterministic=True,
        )
