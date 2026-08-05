import pytest

from runtime.candidate_evaluator import (
    evaluate_candidate_basins,
)
from runtime.candidate_generation import (
    CandidateGenerationResult,
    GeneratedBasinCandidate,
    generate_candidate_basins,
)
from runtime.executor import ConstitutionalViolationError
from runtime.ingress_payload import GovernedIngressPayload
from runtime.recognition_unit import (
    RecognitionUnit,
    instantiate_recognition_unit,
)


def make_unit(
    observation: str = "My system won't shut off.",
) -> RecognitionUnit:
    payload = GovernedIngressPayload(
        payload_id="ING-001",
        raw_observation=observation,
        source_type="user_report",
    )

    return instantiate_recognition_unit(payload)


def test_evaluator_scores_generated_candidates():
    unit = make_unit()
    generation = generate_candidate_basins(unit)

    evaluation = evaluate_candidate_basins(
        generation=generation,
        recognition_unit=unit,
    )

    scores = {
        candidate.basin_id: candidate.evidence_score
        for candidate in evaluation.candidates
    }

    assert scores == {
        "REC-002": 1.0,
        "REC-007": 0.50,
    }


def test_evaluator_preserves_candidate_population():
    unit = make_unit()
    generation = generate_candidate_basins(unit)

    evaluation = evaluate_candidate_basins(
        generation=generation,
        recognition_unit=unit,
    )

    generated_ids = {
        candidate.basin_id
        for candidate in generation.candidates
    }

    evaluated_ids = {
        candidate.basin_id
        for candidate in evaluation.candidates
    }

    assert evaluated_ids == generated_ids


def test_evaluator_identity_is_reproducible():
    unit = make_unit()
    generation = generate_candidate_basins(unit)

    first = evaluate_candidate_basins(
        generation=generation,
        recognition_unit=unit,
    )

    second = evaluate_candidate_basins(
        generation=generation,
        recognition_unit=unit,
    )

    assert first == second
    assert first.evaluation_id == second.evaluation_id


def test_evaluator_rejects_lineage_mismatch():
    unit = make_unit()
    generation = generate_candidate_basins(unit)

    different_unit = RecognitionUnit(
        recognition_unit_id="RU-DIFFERENT",
        literal_observation=unit.literal_observation,
        ingress_payload_id=unit.ingress_payload_id,
        ingress_payload_digest=unit.ingress_payload_digest,
    )

    with pytest.raises(
        ConstitutionalViolationError,
        match="identities do not match",
    ):
        evaluate_candidate_basins(
            generation=generation,
            recognition_unit=different_unit,
        )


def test_evaluator_rejects_unknown_generated_basin():
    unit = make_unit()

    generation = CandidateGenerationResult(
        generation_id="CBG-UNKNOWN",
        recognition_unit_id=unit.recognition_unit_id,
        candidates=(
            GeneratedBasinCandidate(
                basin_id="REC-999",
                eligibility_basis=(
                    "phrase:unknown",
                ),
            ),
        ),
    )

    with pytest.raises(
        ConstitutionalViolationError,
        match="No evaluator rule exists",
    ):
        evaluate_candidate_basins(
            generation=generation,
            recognition_unit=unit,
        )