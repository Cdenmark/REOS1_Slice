from runtime.recognition_result import (
	BasinOrientation,
	Provenance,
	RecognitionResult,
)


def test_recognition_result_creation():

	orientation = BasinOrientation(
		primary_basin="REC-004"
	)

	provenance = Provenance(
		ingress_payload_id="ING-001",
		contract_version="REOS-001"
	)

	result = RecognitionResult(
		recognition_id="RR-001",
		recognition_unit_id="RU-001",
		orientation=orientation,
		resolution_state="oriented",
		provenance=provenance,
	)

	assert result.orientation.primary_basin == "REC-004"

	assert result.resolution_state == "oriented"

	assert result.provenance.contract_version == "REOS-001"
