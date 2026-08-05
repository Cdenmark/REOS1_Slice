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
from runtime.executor import OperationExecutor
from runtime.ingress_payload import GovernedIngressPayload
from runtime.recognition_result import RecognitionResult
from runtime.recognition_unit import (
    RecognitionUnit,
    instantiate_recognition_unit,
)
from runtime.result_assembler import (
    ResultAssemblyInputs,
    assemble_recognition_result,
)
from runtime.transition import derive_transition_id
from runtime.transition_telemetry import TransitionTelemetry
from runtime.vs002_telemetry import (
    VS002TelemetryInputs,
    emit_vs002_telemetry,
)


@dataclass
class REOS002Runtime:
    """
    Passive orchestrator for REOS Vertical Slice 002.

    Jurisdiction:
    - enforce contract-authorized operations;
    - sequence constitutionally bounded stages;
    - return immutable result and telemetry artifacts.

    Prohibited:
    - candidate discovery logic;
    - evidence scoring;
    - basin selection logic;
    - result interpretation;
    - telemetry interpretation.
    """

    runtime_version: str = "reos-runtime-0.2.0"

    def execute(
        self,
        contract: TransitionContract,
        payload: GovernedIngressPayload,
    ) -> Tuple[RecognitionResult, TransitionTelemetry]:
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
            unit = state["recognition_unit"]

            if not isinstance(unit, RecognitionUnit):
                raise TypeError(
                    "Recognition Unit is unavailable for candidate generation."
                )

            generation = generate_candidate_basins(unit)
            state["generation"] = generation
            return generation

        def evaluate_candidates() -> CandidateBasinEvaluation:
            unit = state["recognition_unit"]
            generation = state["generation"]

            if not isinstance(unit, RecognitionUnit):
                raise TypeError(
                    "Recognition Unit is unavailable for candidate evaluation."
                )

            if not isinstance(
                generation,
                CandidateGenerationResult,
            ):
                raise TypeError(
                    "Candidate generation result is unavailable for evaluation."
                )

            evaluation = evaluate_candidate_basins(
                generation=generation,
                recognition_unit=unit,
            )

            state["evaluation"] = evaluation
            return evaluation

        def determine_basin() -> BasinSelection:
            evaluation = state["evaluation"]

            if not isinstance(
                evaluation,
                CandidateBasinEvaluation,
            ):
                raise TypeError(
                    "Candidate evaluation is unavailable for selection."
                )

            selection = select_primary_basin(evaluation)
            state["selection"] = selection
            return selection

        def record_rejections() -> tuple:
            selection = state["selection"]

            if not isinstance(selection, BasinSelection):
                raise TypeError(
                    "Basin selection is unavailable for rejection recording."
                )

            return selection.rejected_basins

        def assemble_result() -> RecognitionResult:
            unit = state["recognition_unit"]
            evaluation = state["evaluation"]
            selection = state["selection"]

            if not isinstance(unit, RecognitionUnit):
                raise TypeError(
                    "Recognition Unit is unavailable for result assembly."
                )

            if not isinstance(
                evaluation,
                CandidateBasinEvaluation,
            ):
                raise TypeError(
                    "Candidate evaluation is unavailable for result assembly."
                )

            if not isinstance(selection, BasinSelection):
                raise TypeError(
                    "Basin selection is unavailable for result assembly."
                )

            result = assemble_recognition_result(
                ResultAssemblyInputs(
                    transition_id=transition_id,
                    contract=contract,
                    payload=payload,
                    recognition_unit=unit,
                    evaluation=evaluation,
                    selection=selection,
                )
            )

            state["result"] = result
            return result

        def emit_telemetry() -> TransitionTelemetry:
            unit = state["recognition_unit"]
            generation = state["generation"]
            evaluation = state["evaluation"]
            selection = state["selection"]
            result = state["result"]

            if not isinstance(unit, RecognitionUnit):
                raise TypeError(
                    "Recognition Unit is unavailable for telemetry emission."
                )

            if not isinstance(
                generation,
                CandidateGenerationResult,
            ):
                raise TypeError(
                    "Candidate generation result is unavailable for telemetry emission."
                )

            if not isinstance(
                evaluation,
                CandidateBasinEvaluation,
            ):
                raise TypeError(
                    "Candidate evaluation is unavailable for telemetry emission."
                )

            if not isinstance(selection, BasinSelection):
                raise TypeError(
                    "Basin selection is unavailable for telemetry emission."
                )

            if not isinstance(result, RecognitionResult):
                raise TypeError(
                    "Recognition Result is unavailable for telemetry emission."
                )

            return emit_vs002_telemetry(
                VS002TelemetryInputs(
                    transition_id=transition_id,
                    contract=contract,
                    payload_digest=payload.digest(),
                    recognition_unit=unit,
                    generation=generation,
                    evaluation=evaluation,
                    selection=selection,
                    result=result,
                    runtime_version=self.runtime_version,
                )
            )

        executor = OperationExecutor(
            operations={
                "ingress_hash": ingress_hash,
                "instantiate_recognition_unit": instantiate_unit,
                "generate_candidate_basins": generate_candidates,
                "evaluate_candidate_basins": evaluate_candidates,
                "determine_primary_basin": determine_basin,
                "record_rejected_basins": record_rejections,
                "assemble_recognition_result": assemble_result,
                "emit_transition_telemetry": emit_telemetry,
            }
        )

        executor.execute_operation(
            contract=contract,
            operation_name="ingress_hash",
        )

        executor.execute_operation(
            contract=contract,
            operation_name="instantiate_recognition_unit",
        )

        executor.execute_operation(
            contract=contract,
            operation_name="generate_candidate_basins",
        )

        executor.execute_operation(
            contract=contract,
            operation_name="evaluate_candidate_basins",
        )

        executor.execute_operation(
            contract=contract,
            operation_name="determine_primary_basin",
        )

        executor.execute_operation(
            contract=contract,
            operation_name="record_rejected_basins",
        )

        result = executor.execute_operation(
            contract=contract,
            operation_name="assemble_recognition_result",
        )

        telemetry = executor.execute_operation(
            contract=contract,
            operation_name="emit_transition_telemetry",
        )

        if not isinstance(result, RecognitionResult):
            raise TypeError(
                "Result assembly did not emit a RecognitionResult."
            )

        if not isinstance(telemetry, TransitionTelemetry):
            raise TypeError(
                "Telemetry emission did not emit TransitionTelemetry."
            )

        return result, telemetry