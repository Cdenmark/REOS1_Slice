from runtime.transition_telemetry import (
	ArtifactLineage,
	OperationTraceEntry,
	RejectedBasin,
	TransitionTelemetry,
)


def test_transition_telemetry_creation():
	telemetry = TransitionTelemetry(
		trace_id="TRACE-001",
		transition_id="REOS-001",
		declaration_hash="a" * 64,
		constitution_version="2.0.0",
		compiler_version="compiler-0.1.0",
		contract_version="1.0.0",
		runtime_version="reos-runtime-0.1.0",
		operation_trace=[
			OperationTraceEntry(
				sequence=1,
				operation_name="ingress_hash",
			)
		],
		candidate_basins=["REC-001", "REC-002"],
		selected_basin="REC-002",
		rejected_basins=[
			RejectedBasin(
				basin_id="REC-001",
				rejection_reason="boundary_mismatch",
			)
		],
		lineage=ArtifactLineage(
			parent_artifacts=[
				"payload-digest",
				"contract-digest",
			],
			produced_by="runtime:reos-runtime-0.1.0",
			certified_by="compiler:compiler-0.1.0",
		),
	)

	assert telemetry.selected_basin == "REC-002"
	assert telemetry.operation_trace[0].operation_name == "ingress_hash"
	assert telemetry.lineage is not None
	assert telemetry.lineage.parent_artifacts == [
		"payload-digest",
		"contract-digest",
	]
