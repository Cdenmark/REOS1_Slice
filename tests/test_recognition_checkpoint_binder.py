from dataclasses import FrozenInstanceError, asdict, fields, replace

import pytest

from contracts.transition_contract import (
    AuthorityMetadata,
    TransitionContract,
)
from foundation.canonical import canonical_hash
from runtime.basin_selector import select_primary_basin
from runtime.candidate_basin_evaluation import (
    CandidateBasin,
    CandidateBasinEvaluation,
)
from runtime.candidate_generation import (
    CandidateGenerationResult,
    GeneratedBasinCandidate,
)
from runtime.governed_noun_authorization import (
    GovernedNounAuthorizationEntry,
    GovernedNounAuthorizationEnvelope,
)
from runtime.ingress_payload import GovernedIngressPayload
from runtime.orientation_resolution import resolve_orientation
from runtime.recognition_result import (
    BasinOrientation,
    Provenance,
    RecognitionResult,
)
from runtime.recognition_unit import instantiate_recognition_unit
from runtime.seam_activation import (
    SeamDetectionParameters,
    detect_seam_activation,
)
from runtime.seam_aware_recognition_result import (
    SeamAwareRecognitionResult,
    assemble_seam_aware_recognition_result,
)
from runtime.transition import derive_transition_id
from runtime.vs003_telemetry import emit_vs003_transition_telemetry
from runtime.movement_types import FrozenRecognitionBundle

from runtime.recognition_checkpoint_binder import (  # noqa: F401
    RecognitionCheckpointBinder,
)


def make_contract(*, allow_authorization: bool = True) -> TransitionContract:
    return TransitionContract(
        contract_id="CONTRACT-REOS-004",
        transition_id="REOS-004",
        authority=AuthorityMetadata(
            declaration_id="REOS-004",
            declaration_hash="a" * 64,
            compiler_release="compiler-0.4.0",
            compiler_digest="b" * 64,
            generated_at="2026-08-08T00:00:00+00:00",
        ),
        constitution_version="2.0.0",
        contract_version="4.0.0",
        allowed_operations=(
            [
                "ingress_hash",
                "instantiate_recognition_unit",
                "generate_candidate_basins",
                "evaluate_candidate_basins",
                "determine_primary_basin",
                "record_rejected_basins",
                "detect_seam_activation",
                "resolve_orientation",
                "assemble_recognition_result",
                "emit_transition_telemetry",
                "bind_recognition_checkpoint",
            ]
            if allow_authorization
            else ["ingress_hash"]
        ),
        permitted_exports=[
            "frozen_recognition_bundle",
            "verified_topology_bundle",
        ],
        prohibited_exports=[
            "execute_shunt",
            "remedy_selection",
            "protocol_generation",
        ],
        operation_parameters={
            "bind_recognition_checkpoint": {
                "required_artifact_count": 5,
                "required_artifact_kinds": [
                    "CANDIDATE_BASIN_EVALUATION",
                    "BASIN_SELECTION",
                    "SEAM_ACTIVATION_CONDITION",
                    "ORIENTATION_RESOLUTION",
                    "SEAM_AWARE_RECOGNITION_RESULT",
                ],
            }
        },
    )


def make_payload() -> GovernedIngressPayload:
    return GovernedIngressPayload(
        payload_id="ING-004",
        raw_observation="My system won't shut off.",
        source_type="user_report",
    )


def make_artifact_chain():
    contract = make_contract()
    payload = make_payload()
    unit = instantiate_recognition_unit(payload)

    generation = CandidateGenerationResult(
        generation_id="CBG-004",
        recognition_unit_id=unit.recognition_unit_id,
        candidates=(
            GeneratedBasinCandidate(
                basin_id="REC-002",
                eligibility_basis=(
                    "phrase:shut off",
                    "mechanic:governor_failure",
                ),
            ),
            GeneratedBasinCandidate(
                basin_id="REC-007",
                eligibility_basis=(
                    "phrase:system",
                    "mechanic:processing_reference",
                ),
            ),
        ),
    )

    evaluation = CandidateBasinEvaluation(
        evaluation_id="CBE-004",
        recognition_unit_id=unit.recognition_unit_id,
        candidates=(
            CandidateBasin(
                basin_id="REC-002",
                evidence_score=0.82,
                evidence_basis=(
                    "phrase:shut off",
                    "mechanic:governor_failure",
                ),
            ),
            CandidateBasin(
                basin_id="REC-007",
                evidence_score=0.76,
                evidence_basis=(
                    "phrase:system",
                    "mechanic:processing_reference",
                ),
            ),
        ),
    )

    selection = select_primary_basin(evaluation)

    seam_condition = detect_seam_activation(
        evaluation=evaluation,
        recognition_unit=unit,
        contract=contract,
        parameters=SeamDetectionParameters(
            maximum_score_gap=0.10,
            minimum_top_score=0.50,
            required_participant_count=2,
        ),
    )

    orientation_resolution = resolve_orientation(
        selection=selection,
        seam_condition=seam_condition,
    )

    base_result = RecognitionResult(
        recognition_id="RR-004",
        recognition_unit_id=unit.recognition_unit_id,
        orientation=BasinOrientation(
            primary_basin=selection.primary_basin,
        ),
        resolution_state="oriented",
        residual_observations=[],
        provenance=Provenance(
            ingress_payload_id=payload.payload_id,
            contract_version=contract.contract_version,
        ),
    )

    result = assemble_seam_aware_recognition_result(
        base_result=base_result,
        orientation_resolution=orientation_resolution,
    )

    transition_id = derive_transition_id(
        contract=contract,
        payload=payload,
    )

    telemetry = emit_vs003_transition_telemetry(
        transition_id=transition_id,
        recognition_unit=unit,
        generation=generation,
        evaluation=evaluation,
        selection=selection,
        seam_condition=seam_condition,
        orientation_resolution=orientation_resolution,
        result=result,
        contract=contract,
    )

    return {
        "contract": contract,
        "payload": payload,
        "unit": unit,
        "generation": generation,
        "evaluation": evaluation,
        "selection": selection,
        "seam_condition": seam_condition,
        "orientation_resolution": orientation_resolution,
        "base_result": base_result,
        "result": result,
        "telemetry": telemetry,
    }


def make_authorization_entry(
    *,
    contract_digest: str,
    artifact_ref: str,
    artifact_digest: str,
    governed_noun_declaration_id: str,
    governed_noun_symbolic_name: str,
    verification_report_id: str,
    verification_report_digest: str,
) -> GovernedNounAuthorizationEntry:
    authorization_digest = GovernedNounAuthorizationEntry(
        artifact_ref=artifact_ref,
        artifact_digest=artifact_digest,
        governed_noun_declaration_id=governed_noun_declaration_id,
        governed_noun_symbolic_name=governed_noun_symbolic_name,
        verification_report_id=verification_report_id,
        verification_report_digest=verification_report_digest,
        authorization_digest="c" * 64,
    ).recompute_authorization_digest(contract_digest)

    return GovernedNounAuthorizationEntry(
        artifact_ref=artifact_ref,
        artifact_digest=artifact_digest,
        governed_noun_declaration_id=governed_noun_declaration_id,
        governed_noun_symbolic_name=governed_noun_symbolic_name,
        verification_report_id=verification_report_id,
        verification_report_digest=verification_report_digest,
        authorization_digest=authorization_digest,
    )


def make_valid_authorization_envelope(artifacts: dict[str, object]):
    contract: TransitionContract = artifacts["contract"]
    evaluation: CandidateBasinEvaluation = artifacts["evaluation"]
    selection = artifacts["selection"]
    seam_condition = artifacts["seam_condition"]
    orientation_resolution = artifacts["orientation_resolution"]
    result = artifacts["result"]

    verification_report_id = "VR3-004"
    verification_report_digest = canonical_hash(
        {
            "report_family": "VS003VerificationReport",
            "orientation_resolution_id": orientation_resolution.resolution_id,
            "selection_id": selection.selection_id,
            "seam_condition_id": seam_condition.condition_id,
            "evaluation_id": evaluation.evaluation_id,
        }
    )

    entries = (
        make_authorization_entry(
            contract_digest=contract.digest(),
            artifact_ref=evaluation.evaluation_id,
            artifact_digest=canonical_hash(asdict(evaluation)),
            governed_noun_declaration_id="REOS-004",
            governed_noun_symbolic_name="CandidateBasinEvaluation",
            verification_report_id=verification_report_id,
            verification_report_digest=verification_report_digest,
        ),
        make_authorization_entry(
            contract_digest=contract.digest(),
            artifact_ref=selection.selection_id,
            artifact_digest=canonical_hash(asdict(selection)),
            governed_noun_declaration_id="REOS-004",
            governed_noun_symbolic_name="BasinSelection",
            verification_report_id=verification_report_id,
            verification_report_digest=verification_report_digest,
        ),
        make_authorization_entry(
            contract_digest=contract.digest(),
            artifact_ref=seam_condition.condition_id,
            artifact_digest=canonical_hash(asdict(seam_condition)),
            governed_noun_declaration_id="REOS-004",
            governed_noun_symbolic_name="SeamActivationCondition",
            verification_report_id=verification_report_id,
            verification_report_digest=verification_report_digest,
        ),
        make_authorization_entry(
            contract_digest=contract.digest(),
            artifact_ref=orientation_resolution.resolution_id,
            artifact_digest=canonical_hash(asdict(orientation_resolution)),
            governed_noun_declaration_id="REOS-004",
            governed_noun_symbolic_name="OrientationResolution",
            verification_report_id=verification_report_id,
            verification_report_digest=verification_report_digest,
        ),
        make_authorization_entry(
            contract_digest=contract.digest(),
            artifact_ref=result.result_id,
            artifact_digest=canonical_hash(asdict(result)),
            governed_noun_declaration_id="REOS-004",
            governed_noun_symbolic_name="SeamAwareRecognitionResult",
            verification_report_id=verification_report_id,
            verification_report_digest=verification_report_digest,
        ),
    )

    return GovernedNounAuthorizationEnvelope(
        transition_contract_ref=contract.contract_id,
        contract_digest=contract.digest(),
        authorization_entries=entries,
        envelope_digest=canonical_hash(
            {
                "transition_contract_ref": contract.contract_id,
                "contract_digest": contract.digest(),
                "authorization_entry_digests": sorted(
                    entry.authorization_digest for entry in entries
                ),
            }
        ),
    )


def _expected_binding_inputs(artifacts: dict[str, object]):
    return {
        "candidate_evaluation_ref": artifacts["evaluation"].evaluation_id,
        "basin_selection_ref": artifacts["selection"].selection_id,
        "seam_activation_condition_ref": artifacts["seam_condition"].condition_id,
        "orientation_resolution_ref": artifacts["orientation_resolution"].resolution_id,
        "seam_aware_result_ref": artifacts["result"].result_id,
        "recognition_unit_id": artifacts["unit"].recognition_unit_id,
    }


def _binder():
    return RecognitionCheckpointBinder()


def _bind_checkpoint(*, artifacts: dict[str, object], envelope, contract):
    binder = _binder()
    return binder.bind_recognition_checkpoint(
        candidate_evaluation=artifacts["evaluation"],
        basin_selection=artifacts["selection"],
        seam_activation_condition=artifacts["seam_condition"],
        orientation_resolution=artifacts["orientation_resolution"],
        seam_aware_recognition_result=artifacts["result"],
        authorization_envelope=envelope,
        contract=contract,
    )


def test_controlled_frozen_bundle_noun_shape():
    field_names = tuple(
        field.name
        for field in fields(FrozenRecognitionBundle)
    )

    assert field_names == (
        "bundle_id",
        "recognition_unit_id",
        "candidate_evaluation_ref",
        "basin_selection_ref",
        "seam_activation_condition_ref",
        "orientation_resolution_ref",
        "seam_aware_result_ref",
        "artifact_bindings",
        "recognition_checkpoint_digest",
        "deterministic",
    )


def test_module_is_initially_red_due_to_missing_production_module():
    assert RecognitionCheckpointBinder is not None


def test_authorization_firewall_reason_codes_are_not_binder_vocab():
    binder_vocab = {
        "AUTH_EVIDENCE_INVALID",
        "AUTH_CONTEXT_INVALID",
        "AUTH_REPRESENTATION_INVALID",
        "AUTH_VERIFICATION_INVALID",
        "AUTH_VERIFICATION_COVERAGE_INVALID",
        "AUTH_GOVERNED_NOUN_CORRESPONDENCE_INVALID",
        "AUTH_IDENTITY_COHERENCE_INVALID",
    }

    assert binder_vocab.isdisjoint(
        {
            "MISSING_REQUIRED_ARTIFACT",
            "ARTIFACT_TYPE_MISMATCH",
            "RECOGNITION_UNIT_MISMATCH",
            "EVALUATION_LINEAGE_MISMATCH",
            "SELECTION_LINEAGE_MISMATCH",
            "SEAM_LINEAGE_MISMATCH",
            "ORIENTATION_LINEAGE_MISMATCH",
            "BASE_RESULT_RECOGNITION_UNIT_MISMATCH",
            "BASE_RESULT_SELECTION_OUTCOME_MISMATCH",
            "ARTIFACT_SET_MISMATCH",
            "DUPLICATE_ARTIFACT_KIND",
            "DUPLICATE_ARTIFACT_ID",
            "CANONICAL_SEQUENCE_VIOLATION",
            "DIGEST_CONSTRUCTION_FAILURE",
        }
    )


def test_valid_checkpoint_chain_preserves_expected_identity_surface():
    artifacts = make_artifact_chain()
    envelope = make_valid_authorization_envelope(artifacts)
    contract = artifacts["contract"]

    assert envelope.transition_contract_ref == contract.contract_id
    assert envelope.contract_digest == contract.digest()
    assert len(envelope.authorization_entries) == 5

    expected_refs = _expected_binding_inputs(artifacts)
    assert expected_refs == {
        "candidate_evaluation_ref": artifacts["evaluation"].evaluation_id,
        "basin_selection_ref": artifacts["selection"].selection_id,
        "seam_activation_condition_ref": artifacts["seam_condition"].condition_id,
        "orientation_resolution_ref": artifacts["orientation_resolution"].resolution_id,
        "seam_aware_result_ref": artifacts["result"].result_id,
        "recognition_unit_id": artifacts["unit"].recognition_unit_id,
    }


def test_authorization_envelope_extra_entries_do_not_imply_checkpoint_membership():
    artifacts = make_artifact_chain()
    envelope = make_valid_authorization_envelope(artifacts)
    contract = artifacts["contract"]

    extra_entry = make_authorization_entry(
        contract_digest=contract.digest(),
        artifact_ref="SARR-EXTRA",
        artifact_digest="f" * 64,
        governed_noun_declaration_id="REOS-004",
        governed_noun_symbolic_name="SeamAwareRecognitionResult",
        verification_report_id="VR3-004",
        verification_report_digest="e" * 64,
    )

    augmented_envelope = GovernedNounAuthorizationEnvelope(
        transition_contract_ref=envelope.transition_contract_ref,
        contract_digest=envelope.contract_digest,
        authorization_entries=envelope.authorization_entries + (extra_entry,),
        envelope_digest=canonical_hash(
            {
                "transition_contract_ref": envelope.transition_contract_ref,
                "contract_digest": envelope.contract_digest,
                "authorization_entry_digests": sorted(
                    entry.authorization_digest
                    for entry in envelope.authorization_entries + (extra_entry,)
                ),
            }
        ),
    )

    assert len(augmented_envelope.authorization_entries) == 6
    assert augmented_envelope.authorization_entries[-1] == extra_entry


def test_checkpoint_artifact_order_is_not_derived_from_authorization_entry_order():
    artifacts = make_artifact_chain()
    envelope = make_valid_authorization_envelope(artifacts)
    reversed_envelope = GovernedNounAuthorizationEnvelope(
        transition_contract_ref=envelope.transition_contract_ref,
        contract_digest=envelope.contract_digest,
        authorization_entries=tuple(reversed(envelope.authorization_entries)),
        envelope_digest=canonical_hash(
            {
                "transition_contract_ref": envelope.transition_contract_ref,
                "contract_digest": envelope.contract_digest,
                "authorization_entry_digests": sorted(
                    entry.authorization_digest
                    for entry in reversed(envelope.authorization_entries)
                ),
            }
        ),
    )

    assert envelope.recompute_envelope_digest() == reversed_envelope.recompute_envelope_digest()


def test_frozen_bundle_is_immutable_and_has_no_authorization_leak_fields():
    assert FrozenRecognitionBundle.__dataclass_params__.frozen is True

    prohibited = {
        "authorization_envelope",
        "authorization_entries",
        "authorization_digest",
        "verification_report_id",
        "verification_report_digest",
    }

    assert prohibited.isdisjoint({field.name for field in fields(FrozenRecognitionBundle)})


def test_binder_witness_file_exposes_expected_red_state_only():
    assert SeamAwareRecognitionResult is not None
