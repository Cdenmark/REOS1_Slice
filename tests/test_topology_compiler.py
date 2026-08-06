import pytest

from compiler.topology_compiler import (
    TopologyCompilationError,
    TopologyCompiler,
)
from foundation.topology_types import (
    DirectedTransitionEdge,
)
from verifier.topology_verifier import (
    CleanRoomTopologyVerifier,
)


def make_edge(
    *,
    edge_id: str = "EDGE-001",
    source_basin: str = "REC-002",
    target_basin: str = "REC-007",
    relationship_type: str = (
        "DIRECT_MOVEMENT_ELIGIBILITY"
    ),
    status: str = "RATIFIED",
    authority_ref: str = "EDGE-DECL-001",
) -> DirectedTransitionEdge:
    return DirectedTransitionEdge(
        edge_id=edge_id,
        source_basin=source_basin,
        target_basin=target_basin,
        relationship_type=relationship_type,
        authority_ref=authority_ref,
        status=status,
    )


def compile_topology(
    *,
    basin_ids: tuple[str, ...] = (
        "REC-002",
        "REC-005",
        "REC-007",
    ),
    edges: tuple[
        DirectedTransitionEdge,
        ...
    ] | None = None,
):
    return TopologyCompiler.compile(
        topology_id="TT-REOS-001",
        topology_version="1.0.0",
        topology_declaration_id=(
            "REOS-TOPOLOGY-001"
        ),
        topology_declaration_version="1.0.0",
        topology_declaration_digest="d" * 64,
        basin_registry_id="BR-REOS-001",
        basin_registry_digest="a" * 64,
        basin_ids=basin_ids,
        edge_declarations=(
            (
                make_edge(
                    edge_id="EDGE-001",
                    source_basin="REC-002",
                    target_basin="REC-005",
                    authority_ref="EDGE-DECL-001",
                ),
                make_edge(
                    edge_id="EDGE-002",
                    source_basin="REC-002",
                    target_basin="REC-007",
                    authority_ref="EDGE-DECL-002",
                ),
            )
            if edges is None
            else edges
        ),
        compiler_digest="b" * 64,
    )


def test_compiler_emits_topology_and_provenance():
    topology, provenance = compile_topology()

    assert topology.topology_id == "TT-REOS-001"
    assert provenance.topology_id == (
        topology.topology_id
    )
    assert provenance.topology_digest == (
        topology.topology_digest
    )
    assert topology.authority.compiler_release == (
        TopologyCompiler.VERSION
    )


def test_compiler_output_passes_clean_room_verifier():
    topology, provenance = compile_topology()

    report = CleanRoomTopologyVerifier.verify(
        topology=topology,
        provenance=provenance,
    )

    assert report.verification_state == "VERIFIED"
    assert all(
        check.status == "PASS"
        for check in report.checks
    )


def test_compiler_is_deterministic_across_edge_input_order():
    first_edge = make_edge(
        edge_id="EDGE-001",
        source_basin="REC-002",
        target_basin="REC-005",
        authority_ref="EDGE-DECL-001",
    )

    second_edge = make_edge(
        edge_id="EDGE-002",
        source_basin="REC-002",
        target_basin="REC-007",
        authority_ref="EDGE-DECL-002",
    )

    first_topology, first_provenance = (
        compile_topology(
            edges=(
                first_edge,
                second_edge,
            )
        )
    )

    second_topology, second_provenance = (
        compile_topology(
            edges=(
                second_edge,
                first_edge,
            )
        )
    )

    assert first_topology == second_topology
    assert first_provenance == second_provenance


def test_compiler_rejects_unknown_source_basin():
    invalid_edge = make_edge(
        source_basin="REC-UNKNOWN",
    )

    with pytest.raises(
        TopologyCompilationError,
        match="Unknown source basin",
    ):
        compile_topology(
            edges=(invalid_edge,)
        )


def test_compiler_rejects_unknown_target_basin():
    invalid_edge = make_edge(
        target_basin="REC-UNKNOWN",
    )

    with pytest.raises(
        TopologyCompilationError,
        match="Unknown target basin",
    ):
        compile_topology(
            edges=(invalid_edge,)
        )


def test_compiler_rejects_self_directed_edge():
    invalid_edge = make_edge(
        source_basin="REC-002",
        target_basin="REC-002",
    )

    with pytest.raises(
        TopologyCompilationError,
        match="Self-directed edge",
    ):
        compile_topology(
            edges=(invalid_edge,)
        )


def test_compiler_rejects_duplicate_edge_id():
    first = make_edge(
        edge_id="EDGE-001",
        target_basin="REC-005",
    )

    second = make_edge(
        edge_id="EDGE-001",
        target_basin="REC-007",
    )

    with pytest.raises(
        TopologyCompilationError,
        match="Duplicate edge_id",
    ):
        compile_topology(
            edges=(first, second)
        )


def test_compiler_rejects_duplicate_directed_relationship():
    first = make_edge(
        edge_id="EDGE-001",
        target_basin="REC-007",
    )

    second = make_edge(
        edge_id="EDGE-002",
        target_basin="REC-007",
    )

    with pytest.raises(
        TopologyCompilationError,
        match="Duplicate directed relationship",
    ):
        compile_topology(
            edges=(first, second)
        )


def test_compiler_rejects_unknown_relationship_type():
    invalid_edge = make_edge(
        relationship_type="UNKNOWN_RELATIONSHIP",
    )

    with pytest.raises(
        TopologyCompilationError,
        match="Unauthorized relationship type",
    ):
        compile_topology(
            edges=(invalid_edge,)
        )


def test_compiler_does_not_infer_reverse_edge():
    topology, _ = compile_topology(
        edges=(
            make_edge(
                edge_id="EDGE-001",
                source_basin="REC-002",
                target_basin="REC-005",
            ),
        )
    )

    directed_pairs = {
        (
            edge.source_basin,
            edge.target_basin,
        )
        for edge in topology.directed_edges
    }

    assert (
        "REC-002",
        "REC-005",
    ) in directed_pairs

    assert (
        "REC-005",
        "REC-002",
    ) not in directed_pairs
