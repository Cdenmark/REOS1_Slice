from dataclasses import dataclass
from typing import Tuple

from contracts.transition_contract import TransitionContract
from runtime.basin_selector import (
    BasinSelection,
    select_primary_basin,
)
from runtime.candidate_basin_evaluation import (
    CandidateBasinEvaluation,
)
from runtime.candidate_evaluator import evaluate_candidate_basins
from runtime.candidate_generation import (
    CandidateGenerationResult,
    generate_candidate_basins,
)
from runtime.executor import (
    ConstitutionalViolationError,
    OperationExecutor,
)
from runtime.ingress_payload import GovernedIngressPayload
from runtime.orientation_resolution import (
    OrientationResolution,
    resolve_orientation,
)
from runtime.recognition_unit import (
    RecognitionUnit,
    instantiate_recognition_unit,
)
from runtime.seam_activation import (
    SeamActivationCondition,
    SeamDetectionParameters,
    detect_seam_activation,
)
from runtime.seam_aware_recognition_result import (
    SeamAwareRecognitionResult,
    assemble_seam_aware_recognition_result,
)
from runtime.serializer import canonical_hash
from runtime.transition import derive_transition_id
from runtime.vs003_telemetry import (
    VS003TransitionTelemetry,
    emit_vs003_transition_telemetry,
)


@dataclass
class TransitionOrchestrator:
    """
    Timeless contract-gated transition orchestrator.

    Jurisdiction:
    - enforce operation authorization;
    - sequence constitutional actors;
    - route immutable artifacts;
    - return final result and telemetry.

    Prohibited:
    - candidate discovery logic;
    - evidence scoring;
    - basin selection logic;
    - seam-threshold invention;
    - orientation resolution logic;
    - result interpretation;
    - telemetry interpretation.
    """

    runtime_version: str = "reos-runtime-0.3.0"

    def execute(
        self,
        contract: TransitionContract,
        payload: GovernedIngressPayload,
    ) -> Tuple[
        SeamAwareRecognitionResult,
        VS003TransitionTelemetry,
    ]:
        transition_id = derive_transition_id(
            contract=contract,
            payload=payload,
        )

        state: dict[str, object] = {}

        def ingress_hash() -> str:
            return payload.digest()

        def instantiate_unit() -> RecognitionUnit:
            unit = instantiate_recognition_unit(payload)
            state["recognition_unit"] = unit
            return unit

        def generate_candidates() -> CandidateGenerationResult:
            unit = state.get("recognition_unit")

            if not isinstance(unit, RecognitionUnit):
                raise ConstitutionalViolationError(
                    "Recognition Unit is unavailable for candidate generation."
                )

            generation = generate_candidate_basins(unit)
            state["generation"] = generation
            return generation

        def evaluate_candidates() -> CandidateBasinEvaluation:
            unit = state.get("recognition_unit")
            generation = state.get("generation")

            if not isinstance(unit, RecognitionUnit):
                raise ConstitutionalViolationError(
                    "Recognition Unit is unavailable for candidate evaluation."
                )

            if not isinstance(
                generation,
                CandidateGenerationResult,
            ):
                raise ConstitutionalViolationError(
                    "Candidate generation result is unavailable for evaluation."
                )

            evaluation = evaluate_candidate_basins(
                generation=generation,
                recognition_unit=unit,
            )

            state["evaluation"] = evaluation
            return evaluation

        def determine_primary_basin() -> BasinSelection:
            evaluation = state.get("evaluation")

            if not isinstance(
                evaluation,
                CandidateBasinEvaluation,
            ):
                raise ConstitutionalViolationError(
                    "Candidate evaluation is unavailable for basin selection."
                )

            selection = select_primary_basin(evaluation)
            state["selection"] = selection
            return selection

        def record_rejected_basins() -> tuple:
            selection = state.get("selection")

            if not isinstance(selection, BasinSelection):
                raise ConstitutionalViolationError(
                    "Basin selection is unavailable for rejection recording."
                )

            return selection.rejected_basins

        def detect_seam() -> SeamActivationCondition:
            unit = state.get("recognition_unit")
            evaluation = state.get("evaluation")

            if not isinstance(unit, RecognitionUnit):
                raise ConstitutionalViolationError(
                    "Recognition Unit is unavailable for seam detection."
                )

            if not isinstance(
                evaluation,
                CandidateBasinEvaluation,
            ):
                raise ConstitutionalViolationError(
                    "Candidate evaluation is unavailable for seam detection."
                )

            raw_parameters = contract.operation_parameters.get(
                "detect_seam_activation"
            )

            if raw_parameters is None:
                raise ConstitutionalViolationError(
                    "Missing operation parameters for 'detect_seam_activation'."
                )

            required_keys = {
                "maximum_score_gap",
                "minimum_top_score",
                "required_participant_count",
            }

            missing_keys = required_keys.difference(raw_parameters)

            if missing_keys:
                raise ConstitutionalViolationError(
                    "Missing seam detection parameters: "
                    + ", ".join(sorted(missing_keys))
                )

            parameters = SeamDetectionParameters(
                maximum_score_gap=raw_parameters[
                    "maximum_score_gap"
                ],
                minimum_top_score=raw_parameters[
                    "minimum_top_score"
                ],
                required_participant_count=raw_parameters[
                    "required_participant_count"
                ],
            )

            seam_condition = detect_seam_activation(
                evaluation=evaluation,
                recognition_unit=unit,
                contract=contract,
                parameters=parameters,
            )

            state["seam_condition"] = seam_condition
            return seam_condition

        def resolve_final_orientation() -> OrientationResolution:
            selection = state.get("selection")
            seam_condition = state.get("seam_condition")

            if not isinstance(selection, BasinSelection):
                raise ConstitutionalViolationError(
                    "Basin selection is unavailable for orientation resolution."
                )

            if not isinstance(
                seam_condition,
                SeamActivationCondition,
            ):
                raise ConstitutionalViolationError(
                    "Seam condition is unavailable for orientation resolution."
                )

            resolution = resolve_orientation(
                selection=selection,
                seam_condition=seam_condition,
            )

            state["orientation_resolution"] = resolution
            return resolution

        def assemble_result() -> SeamAwareRecognitionResult:
            unit = state.get("recognition_unit")
            selection = state.get("selection")
            resolution = state.get("orientation_resolution")

            if not isinstance(unit, RecognitionUnit):
                raise ConstitutionalViolationError(
                    "Recognition Unit is unavailable for result assembly."
                )

            if not isinstance(selection, BasinSelection):
                raise ConstitutionalViolationError(
                    "Basin selection is unavailable for result assembly."
                )

            if not isinstance(
                resolution,
                OrientationResolution,
            ):
                raise ConstitutionalViolationError(
                    "Orientation resolution is unavailable for result assembly."
                )

            base_result_id = (
                "RR-"
                + canonical_hash(
                    {
                        "transition_id": transition_id,
                        "recognition_unit_id": (
                            unit.recognition_unit_id
                        ),
                        "primary_basin": selection.primary_basin,
                    }
                )[:16].upper()
            )

            from runtime.recognition_result import (
                BasinOrientation,
                Provenance,
                RecognitionResult,
            )

            base_result = RecognitionResult(
                recognition_id=base_result_id,
                recognition_unit_id=unit.recognition_unit_id,
                orientation=BasinOrientation(
                    primary_basin=selection.primary_basin,
                    active_seam=None,
                    directional_momentum=None,
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
                orientation_resolution=resolution,
            )

            state["result"] = result
            return result

        def emit_telemetry() -> VS003TransitionTelemetry:
            unit = state.get("recognition_unit")
            generation = state.get("generation")
            evaluation = state.get("evaluation")
            selection = state.get("selection")
            seam_condition = state.get("seam_condition")
            resolution = state.get("orientation_resolution")
            result = state.get("result")

            if not isinstance(unit, RecognitionUnit):
                raise ConstitutionalViolationError(
                    "Recognition Unit is unavailable for telemetry emission."
                )

            if not isinstance(
                generation,
                CandidateGenerationResult,
            ):
                raise ConstitutionalViolationError(
                    "Candidate generation result is unavailable for telemetry emission."
                )

            if not isinstance(
                evaluation,
                CandidateBasinEvaluation,
            ):
                raise ConstitutionalViolationError(
                    "Candidate evaluation is unavailable for telemetry emission."
                )

            if not isinstance(selection, BasinSelection):
                raise ConstitutionalViolationError(
                    "Basin selection is unavailable for telemetry emission."
                )

            if not isinstance(
                seam_condition,
                SeamActivationCondition,
            ):
                raise ConstitutionalViolationError(
                    "Seam condition is unavailable for telemetry emission."
                )

            if not isinstance(
                resolution,
                OrientationResolution,
            ):
                raise ConstitutionalViolationError(
                    "Orientation resolution is unavailable for telemetry emission."
                )

            if not isinstance(
                result,
                SeamAwareRecognitionResult,
            ):
                raise ConstitutionalViolationError(
                    "Seam-aware result is unavailable for telemetry emission."
                )

            return emit_vs003_transition_telemetry(
                transition_id=transition_id,
                recognition_unit=unit,
                generation=generation,
                evaluation=evaluation,
                selection=selection,
                seam_condition=seam_condition,
                orientation_resolution=resolution,
                result=result,
                contract=contract,
                runtime_version=self.runtime_version,
            )

        executor = OperationExecutor(
            operations={
                "ingress_hash": ingress_hash,
                "instantiate_recognition_unit": instantiate_unit,
                "generate_candidate_basins": generate_candidates,
                "evaluate_candidate_basins": evaluate_candidates,
                "determine_primary_basin": determine_primary_basin,
                "record_rejected_basins": record_rejected_basins,
                "detect_seam_activation": detect_seam,
                "resolve_orientation": resolve_final_orientation,
                "assemble_recognition_result": assemble_result,
                "emit_transition_telemetry": emit_telemetry,
            }
        )

        operation_order = (
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
        )

        outputs: dict[str, object] = {}

        for operation_name in operation_order:
            outputs[operation_name] = executor.execute_operation(
                contract=contract,
                operation_name=operation_name,
            )

        result = outputs["assemble_recognition_result"]
        telemetry = outputs["emit_transition_telemetry"]

        if not isinstance(result, SeamAwareRecognitionResult):
            raise ConstitutionalViolationError(
                "Result assembly did not emit SeamAwareRecognitionResult."
            )

        if not isinstance(
            telemetry,
            VS003TransitionTelemetry,
        ):
            raise ConstitutionalViolationError(
                "Telemetry emission did not emit VS003TransitionTelemetry."
            )

        return result, telemetry
