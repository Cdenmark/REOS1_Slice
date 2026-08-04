from runtime.transition_telemetry import (
	TransitionTelemetry,
	RuleTraceEntry,
	RejectedBasin,
)


def test_transition_telemetry_creation():
	telemetry = TransitionTelemetry(
		trace_id="TRACE-001",
		transition_id="TRN-001",
		declaration_hash="abc123",
		constitution_version="0.1.0",
		compiler_version="0.1.0",
		contract_version="0.1.0",
		runtime_version="0.1.0",
		candidate_basins=["REC-001"],
		selected_basin="REC-001",
		rejected_basins=[
			RejectedBasin(
				basin_id="REC-002",
				rejection_reason="boundary_mismatch",
			)
		],
		rule_trace=[
			RuleTraceEntry(
				sequence=1,
				rule_id="RULE-001",
			)
		],
	)

	assert telemetry.selected_basin == "REC-001"
	assert telemetry.rule_trace[0].rule_id == "RULE-001"
