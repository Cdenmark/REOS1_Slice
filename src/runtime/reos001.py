from dataclasses import dataclass
from typing import Tuple

from contracts.transition_contract import TransitionContract
from runtime.executor import OperationExecutor
from runtime.ingress_payload import GovernedIngressPayload
from runtime.orientation import determine_primary_basin
from runtime.recognition_result import (
    Provenance,
    RecognitionResult,
)
from runtime.recognition_unit import (
    RecognitionUnit,
    instantiate_recognition_unit,
)
from runtime.serializer import canonical_hash
from runtime.transition import derive_transition_id
from runtime.transition_telemetry import (
    ArtifactLineage,
    OperationTraceEntry,
    RejectedBasin,
    TransitionTelemetry,
)


@dataclass
class REOS001Runtime:
    """
    Minimal end-to-end runtime for REOS Vertical Slice 001.

    This runtime executes only contract-authorized operations and emits:
    - one RecognitionResult
    - one TransitionTelemetry record
    """

    runtime_version: str = "reos-runtime-0.1.0"

    def execute(
        self,
        contract: TransitionContract,
        payload: GovernedIngressPayload,
    ) -> Tuple[RecognitionResult, TransitionTelemetry]:
        transition_id = derive_transition_id(
            contract=contract,
            payload=payload,
        )

        recognition_unit_holder: dict[str, RecognitionUnit] = {}
        orientation_holder: dict[str, object] = {}

        executor = OperationExecutor(
            operations={
                "ingress_hash": payload.digest,
                "instantiate_recognition_unit": lambda: (
                    recognition_unit_holder.setdefault(
                        "unit",
                        instantiate_recognition_unit(payload),
                    )
                ),
                "determine_primary_basin": lambda: (
                    orientation_holder.setdefault(
                        "orientation",
                        determine_primary_basin(
                            recognition_unit_holder["unit"]
                        ),
                    )
                ),
            }
        )

        payload_digest = executor.execute_operation(
            contract=contract,
            operation_name="ingress_hash",
        )

        recognition_unit = executor.execute_operation(
            contract=contract,
            operation_name="instantiate_recognition_unit",
        )

        orientation = executor.execute_operation(
            contract=contract,
            operation_name="determine_primary_basin",
        )

        telemetry = TransitionTelemetry(
            trace_id=f"TRACE-{transition_id}",
            transition_id=transition_id,
            declaration_hash=contract.authority.declaration_hash,
            constitution_version=contract.constitution_version,
            compiler_version=contract.authority.compiler_release,
            contract_version=contract.contract_version,
            runtime_version=self.runtime_version,
            operation_trace=[
                OperationTraceEntry(
                    sequence=1,
                    operation_name="ingress_hash",
                ),
                OperationTraceEntry(
                    sequence=2,
                    operation_name="instantiate_recognition_unit",
                ),
                OperationTraceEntry(
                    sequence=3,
                    operation_name="determine_primary_basin",
                ),
            ],
            candidate_basins=["REC-002"],
            selected_basin=orientation.primary_basin,
            rejected_basins=[],
            evaluated_seams=[],
            termination_reason="SINGLE_BASIN_ORIENTATION_SUCCESS",
            lineage=ArtifactLineage(
                parent_artifacts=[
                    payload_digest,
                    contract.digest(),
                ],
                produced_by=f"runtime:{self.runtime_version}",
                certified_by=(
                    f"compiler:{contract.authority.compiler_release}"
                ),
            ),
        )

        recognition_id = (
            "RR-"
            + canonical_hash(
                {
                    "transition_id": transition_id,
                    "recognition_unit_id": (
                        recognition_unit.recognition_unit_id
                    ),
                    "primary_basin": orientation.primary_basin,
                }
            )[:16].upper()
        )

        result = RecognitionResult(
            recognition_id=recognition_id,
            recognition_unit_id=recognition_unit.recognition_unit_id,
            orientation=orientation,
            resolution_state="oriented",
            residual_observations=[],
            provenance=Provenance(
                ingress_payload_id=payload.payload_id,
                contract_version=contract.contract_version,
            ),
        )

        return result, telemetry
