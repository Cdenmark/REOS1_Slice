from dataclasses import FrozenInstanceError

import pytest

from foundation.topology_types import (
    TopologyAuthorityMetadata,
    TransitionTopology,
)
from runtime.movement_types import (
    VerifiedTopologyBundle,
)


@pytest.fixture
def topology_snapshot() -> TransitionTopology:
    authority = TopologyAuthorityMetadata(
        topology_declaration_id="REOS-TOPOLOGY-001",
        topology_declaration_version="1.0.0",
        basin_registry_id="BR-REOS-001",
        basin_registry_digest="c" * 64,
        compiler_release="topology-compiler-1.0.0",
        compiler_digest="d" * 64,
    )

    return TransitionTopology(
        topology_id="TT-REOS-001",
        topology_version="1.0.0",
        topology_digest="a" * 64,
        basin_registry_id="BR-REOS-001",
        basin_registry_digest="c" * 64,
        authority=authority,
        directed_edges=(),
        deterministic=True,
    )


@pytest.fixture
def verified_topology_bundle(
    topology_snapshot: TransitionTopology,
) -> VerifiedTopologyBundle:
    return VerifiedTopologyBundle(
        binding_id="VTB-001",
        topology_ref="TT-REOS-001",
        topology_id="TT-REOS-001",
        topology_version="1.0.0",
        topology_digest="a" * 64,
        topology_snapshot=topology_snapshot,
        bound_contract_id="TC-001",
        bound_contract_digest="b" * 64,
        verification_state="VERIFIED",
        deterministic=True,
    )


def test_verified_topology_bundle_is_immutable(
    verified_topology_bundle: VerifiedTopologyBundle,
):
    with pytest.raises(FrozenInstanceError):
        verified_topology_bundle.binding_id = "VTB-MUTATED"

    with pytest.raises(FrozenInstanceError):
        verified_topology_bundle.topology_digest = "e" * 64

    with pytest.raises(FrozenInstanceError):
        verified_topology_bundle.topology_snapshot = None


def test_verified_topology_bundle_preserves_supplied_fields(
    verified_topology_bundle: VerifiedTopologyBundle,
    topology_snapshot: TransitionTopology,
):
    assert verified_topology_bundle.binding_id == "VTB-001"

    assert (
        verified_topology_bundle.topology_ref
        == "TT-REOS-001"
    )
    assert (
        verified_topology_bundle.topology_id
        == "TT-REOS-001"
    )
    assert (
        verified_topology_bundle.topology_version
        == "1.0.0"
    )
    assert (
        verified_topology_bundle.topology_digest
        == "a" * 64
    )

    assert (
        verified_topology_bundle.topology_snapshot
        is topology_snapshot
    )
    assert isinstance(
        verified_topology_bundle.topology_snapshot,
        TransitionTopology,
    )

    assert (
        verified_topology_bundle.bound_contract_id
        == "TC-001"
    )
    assert (
        verified_topology_bundle.bound_contract_digest
        == "b" * 64
    )

    assert (
        verified_topology_bundle.verification_state
        == "VERIFIED"
    )
    assert verified_topology_bundle.deterministic is True


def test_verified_topology_bundle_contains_no_prohibited_behavior():
    prohibited_methods = {
        "create",
        "bind",
        "build",
        "generate",
        "validate",
        "verify",
        "calculate_digest",
        "derive_digest",
        "check_parity",
        "resolve_topology",
        "load_topology",
    }

    assert prohibited_methods.isdisjoint(
        VerifiedTopologyBundle.__dict__
    )
