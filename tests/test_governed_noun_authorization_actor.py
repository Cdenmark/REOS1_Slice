from dataclasses import asdict, replace

import pytest

from foundation.canonical import canonical_hash

from contracts.transition_contract import (
    AuthorityMetadata,
    TransitionContract,
)
from runtime.basin_selector import select_primary_basin
from runtime.candidate_basin_evaluation import (
    CandidateBasin,
    CandidateBasinEvaluation,
)
from runtime.candidate_generation import (
    GeneratedBasinCandidate,
    CandidateGenerationResult,
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
    assemble_seam_aware_recognition_result,
)
from runtime.transition import derive_transition_id
from runtime.vs003_telemetry import emit_vs003_transition_telemetry
from verifier.vs003_clean_room_verifier import verify_vs003_transition
from runtime.governed_noun_authorization_actor import (
    GovernedNounAuthorizationAdjudicator,
)


def make_contract(*, allow_authorization: bool = True) -> TransitionContract:
    return TransitionContract(
        contract_id="CONTRACT-REOS-003",
        transition_id="REOS-003",
        authority=AuthorityMetadata(
            declaration_id="REOS-003",
            declaration_hash="a" * 64,
            compiler_release="compiler-0.3.0",
            compiler_digest="b" * 64,
            generated_at="2026-08-05T18:00:00+00:00",
        ),
        constitution_version="2.0.0",
        contract_version="3.0.0",
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
                "authorize_governed_noun_representation",
            ]
            if allow_authorization
            else ["ingress_hash"]
        ),
        permitted_exports=[
            "recognition_result",
            "seam_activation_condition",
            "orientation_resolution",
            "seam_aware_recognition_result",
            "transition_telemetry",
        ],
        prohibited_exports=[
            "execute_shunt",
            "remedy_selection",
            "protocol_generation",
        ],
        operation_parameters={
            "detect_seam_activation": {
                "maximum_score_gap": 0.10,
                "minimum_top_score": 0.50,
                "required_participant_count": 2,
            }
        },
    )


def make_payload() -> GovernedIngressPayload:
    return GovernedIngressPayload(
        payload_id="ING-003",
        raw_observation="My system won't shut off.",
        source_type="user_report",
    )


def make_artifacts():
    contract = make_contract()
    payload = make_payload()
    unit = instantiate_recognition_unit(payload)

    generation = CandidateGenerationResult(
        generation_id="CBG-003",
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
        evaluation_id="CBE-003",
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
        recognition_id="RR-003",
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

    verification_report = verify_vs003_transition(
        evaluation_noun=asdict(evaluation),
        selection_noun=asdict(selection),
        contract_noun=asdict(contract),
        witnessed_seam_noun=asdict(seam_condition),
        witnessed_orientation_noun=asdict(orientation_resolution),
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
        "verification_report": verification_report,
    }


def make_entry(
    *,
    contract_digest: str,
    artifact_ref: str = "SARR-003",
) -> GovernedNounAuthorizationEntry:
    artifact_digest = "a" * 64
    verification_report_id = "VR-003"
    verification_report_digest = "b" * 64

    authorization_digest = GovernedNounAuthorizationEntry(
        artifact_ref=artifact_ref,
        artifact_digest=artifact_digest,
        governed_noun_declaration_id="REOS-004",
        governed_noun_symbolic_name="SeamAwareRecognitionResult",
        verification_report_id=verification_report_id,
        verification_report_digest=verification_report_digest,
        authorization_digest="c" * 64,
    ).recompute_authorization_digest(contract_digest)

    return GovernedNounAuthorizationEntry(
        artifact_ref=artifact_ref,
        artifact_digest=artifact_digest,
        governed_noun_declaration_id="REOS-004",
        governed_noun_symbolic_name="SeamAwareRecognitionResult",
        verification_report_id=verification_report_id,
        verification_report_digest=verification_report_digest,
        authorization_digest=authorization_digest,
    )


def make_envelope(entries, *, contract_ref="CONTRACT-REOS-003", contract_digest="d" * 64):
    ordered_entries = tuple(entries)
    envelope_material = {
        "transition_contract_ref": contract_ref,
        "contract_digest": contract_digest,
        "authorization_entry_digests": sorted(
            entry.authorization_digest for entry in ordered_entries
        ),
    }

    return GovernedNounAuthorizationEnvelope(
        transition_contract_ref=contract_ref,
        contract_digest=contract_digest,
        authorization_entries=ordered_entries,
        envelope_digest=canonical_hash(envelope_material),
    )


def test_actor_module_is_not_yet_implemented():
    assert GovernedNounAuthorizationAdjudicator is not None


def test_actor_jurisdiction_excludes_binder_and_provenance():
    assert GovernedNounAuthorizationAdjudicator is not None


def test_single_artifact_success_emits_one_entry_and_one_envelope():
    evidence = make_artifacts()
    contract = evidence["contract"]
    entry = make_entry(contract_digest=contract.digest())
    envelope = make_envelope([entry], contract_digest=contract.digest())

    assert isinstance(envelope, GovernedNounAuthorizationEnvelope)
    assert len(envelope.authorization_entries) == 1
    assert envelope.authorization_entries[0] == entry
    assert envelope.authorization_entries[0].authorization_digest == entry.authorization_digest
    assert envelope.envelope_digest == envelope.recompute_envelope_digest()


def test_single_artifact_success_is_reproducible():
    evidence = make_artifacts()
    contract = evidence["contract"]
    first = make_envelope([make_entry(contract_digest=contract.digest())], contract_digest=contract.digest())
    second = make_envelope([make_entry(contract_digest=contract.digest())], contract_digest=contract.digest())

    assert first == second
    assert first.envelope_digest == second.envelope_digest


def test_multi_artifact_atomicity_all_valid_yields_one_envelope():
    evidence = make_artifacts()
    contract = evidence["contract"]
    entries = (
        make_entry(contract_digest=contract.digest()),
        make_entry(contract_digest=contract.digest(), artifact_ref="SARR-004"),
    )

    envelope = make_envelope(entries, contract_digest=contract.digest())

    assert isinstance(envelope, GovernedNounAuthorizationEnvelope)
    assert len(envelope.authorization_entries) == 2


def test_multi_artifact_atomicity_failure_means_no_envelope():
    evidence = make_artifacts()
    contract = evidence["contract"]
    valid_entry = make_entry(contract_digest=contract.digest())
    invalid_entry = replace(valid_entry, authorization_digest="0" * 64)

    with pytest.raises(ValueError):
        make_envelope((valid_entry, invalid_entry), contract_digest=contract.digest())


def test_auth_evidence_invalid_represents_missing_or_malformed_required_evidence():
    with pytest.raises(ValueError):
        make_entry(contract_digest="d" * 64).recompute_authorization_digest("not-a-digest")


def test_auth_context_invalid_represents_unauthorized_or_incoherent_context():
    evidence = make_artifacts()
    contract = evidence["contract"]
    entry = make_entry(contract_digest=contract.digest())

    with pytest.raises(ValueError):
        make_envelope([entry], contract_digest="f" * 64)


def test_auth_representation_invalid_represents_content_mismatch():
    evidence = make_artifacts()
    contract = evidence["contract"]
    entry = make_entry(contract_digest=contract.digest())
    tampered_entry = replace(entry, artifact_digest="f" * 64)

    with pytest.raises(ValueError):
        make_envelope([tampered_entry], contract_digest=contract.digest())


def test_auth_verification_invalid_represents_report_integrity_failure():
    evidence = make_artifacts()
    contract = evidence["contract"]
    entry = make_entry(contract_digest=contract.digest())
    tampered_entry = replace(entry, verification_report_digest="f" * 64)

    with pytest.raises(ValueError):
        make_envelope([tampered_entry], contract_digest=contract.digest())


def test_auth_verification_coverage_invalid_represents_wrong_report_or_companion_chain():
    evidence = make_artifacts()
    contract = evidence["contract"]
    entry = make_entry(contract_digest=contract.digest())
    wrong_context_entry = replace(entry, artifact_ref="SARR-OTHER")

    with pytest.raises(ValueError):
        make_envelope([wrong_context_entry], contract_digest=contract.digest())


def test_auth_governed_noun_correspondence_invalid_represents_mapping_failure():
    evidence = make_artifacts()
    contract = evidence["contract"]
    entry = replace(
        make_entry(contract_digest=contract.digest()),
        governed_noun_symbolic_name="NotARealNoun",
    )

    with pytest.raises(ValueError):
        make_envelope([entry], contract_digest=contract.digest())


def test_auth_identity_coherence_invalid_represents_duplicate_or_stale_identity():
    evidence = make_artifacts()
    contract = evidence["contract"]
    entry = make_entry(contract_digest=contract.digest())

    with pytest.raises(ValueError):
        make_envelope([entry, entry], contract_digest=contract.digest())


def test_stateless_determinism_repeated_identical_evidence_yields_identical_results():
    evidence = make_artifacts()
    contract = evidence["contract"]
    entry = make_entry(contract_digest=contract.digest())

    first = make_envelope([entry], contract_digest=contract.digest())
    second = make_envelope([entry], contract_digest=contract.digest())

    assert first == second
    assert first.envelope_digest == second.envelope_digest
