from runtime.transition import new_transition_id


def test_transition_id_prefix():
	tid = new_transition_id()

	assert tid.startswith("TRN-")
