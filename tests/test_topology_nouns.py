from dataclasses import FrozenInstanceError, fields

import pytest

from foundation.topology_types import (
    DirectedTransitionEdge,
    TopologyAuthorityMetadata,
    TopologyProvenance,
    TopologyVerificationCheck,
    TopologyVerificationReport,
    TransitionTopology,
)


def make_edge(
    *,
    edge_id: str = "EDGE-001",
    source_basin: str = "REC-002",
    target_basin: str = "REC-007",
) -> DirectedTransitionEdge:
    return DirectedTransitionEdge(
        edge_id=edge_id,
        source_basin=source_basin,
        target_basin=target_basin,
        relationship_type="DIRECT_MOVEMENT_ELIGIBILITY",
        authority_ref="REOS-TOPOLOGY-001",
        status="RATIFIED",
    )


def make_authority() -> TopologyAuthorityMetadata:
    return TopologyAuthorityMetadata(
        topology_declaration_id="REOS-TOPOLOGY-001",
        topology_declaration_version="1.0.0",
        basin_registry_id="BR-REOS-001",
        basin_registry_digest="a" * 64,
        compiler_release="topology-compiler-1.0.0",
        compiler_digest="b" * 64,
    )


def make_topology() -> TransitionTopology:
    return TransitionTopology(
        topology_id="TT-REOS-001",
        topology_version="1.0.0",
        topology_digest="c" * 64,
        basin_registry_id="BR-REOS-001",
        basin_registry_digest="a" * 64,
        authority=make_authority(),
        directed_edges=(
            make_edge(),
            make_edge(
                edge_id="EDGE-002",
                target_basin="REC-005",
            ),
        ),
    )


def test_topology_nouns_are_immutable():
    edge = make_edge()

    with pytest.raises(FrozenInstanceError):
        edge.target_basin = "REC-005"

    topology = make_topology()

    with pytest.raises(FrozenInstanceError):
        topology.topology_id = "TT-DIFFERENT"


def test_transition_edge_preserves_explicit_direction():
    edge = make_edge(
        source_basin="REC-002",
        target_basin="REC-007",
    )

    assert edge.source_basin == "REC-002"
    assert edge.target_basin == "REC-007"
    assert edge.source_basin != edge.target_basin

    reverse_edge = make_edge(
        edge_id="EDGE-REVERSE",
        source_basin="REC-007",
        target_basin="REC-002",
    )

    assert reverse_edge != edge
    assert reverse_edge.source_basin == edge.target_basin
    assert reverse_edge.target_basin == edge.source_basin


def test_transition_topology_preserves_authority_and_registry_lineage():
    topology = make_topology()

    assert topology.authority.topology_declaration_id == (
        "REOS-TOPOLOGY-001"
    )
    assert topology.basin_registry_id == "BR-REOS-001"
    assert topology.basin_registry_digest == "a" * 64
    assert topology.authority.compiler_release == (
        "topology-compiler-1.0.0"
    )
    assert isinstance(topology.directed_edges, tuple)
    assert len(topology.directed_edges) == 2


def test_topology_provenance_preserves_compilation_lineage():
    provenance = TopologyProvenance(
        provenance_id="TPROV-001",
        topology_id="TT-REOS-001",
        topology_digest="c" * 64,
        declaration_refs=(
            "REOS-TOPOLOGY-001",
        ),
        edge_declaration_refs=(
            "EDGE-DECL-001",
            "EDGE-DECL-002",
        ),
        basin_registry_id="BR-REOS-001",
        basin_registry_digest="a" * 64,
        compiler_release="topology-compiler-1.0.0",
        compiler_digest="b" * 64,
    )

    assert provenance.topology_id == "TT-REOS-001"
    assert provenance.topology_digest == "c" * 64
    assert provenance.declaration_refs == (
        "REOS-TOPOLOGY-001",
    )
    assert isinstance(
        provenance.edge_declaration_refs,
        tuple,
    )


def test_topology_verification_report_records_checks_only():
    report = TopologyVerificationReport(
        report_id="TVR-001",
        topology_id="TT-REOS-001",
        topology_digest="c" * 64,
        verifier_version="topology-verifier-1.0.0",
        verification_state="VERIFIED",
        checks=(
            TopologyVerificationCheck(
                check_id="CHK-TOP-001",
                invariant_id="INV-TOP-001",
                status="PASS",
                message="Basin references are valid.",
            ),
            TopologyVerificationCheck(
                check_id="CHK-TOP-002",
                invariant_id="INV-TOP-003",
                status="PASS",
                message="Reverse edges were not inferred.",
            ),
        ),
    )

    assert report.verification_state == "VERIFIED"
    assert all(
        check.status == "PASS"
        for check in report.checks
    )
    assert isinstance(report.checks, tuple)


def test_topology_nouns_contain_no_embedded_compiler_behavior():
    noun_types = (
        DirectedTransitionEdge,
        TopologyAuthorityMetadata,
        TransitionTopology,
        TopologyProvenance,
        TopologyVerificationCheck,
        TopologyVerificationReport,
    )

    prohibited_methods = {
        "create",
        "compile",
        "build",
        "generate",
        "calculate_digest",
        "verify",
    }

    for noun_type in noun_types:
        assert prohibited_methods.isdisjoint(
            set(noun_type.__dict__)
        )

        assert len(fields(noun_type)) > 0
