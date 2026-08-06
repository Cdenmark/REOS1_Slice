from dataclasses import asdict
from typing import Iterable, Mapping, Sequence

from foundation.canonical import canonical_hash
from foundation.topology_types import (
    DirectedTransitionEdge,
    TopologyAuthorityMetadata,
    TopologyProvenance,
    TransitionTopology,
)


class TopologyCompilationError(Exception):
    """Raised when topology compilation violates constitutional invariants."""


class TopologyCompiler:
    """
    Compiler authority for REOS-TOPOLOGY-001.

    Jurisdiction:
    - validate basin references;
    - validate edge declarations;
    - validate relationship types;
    - reject duplicate directed edges;
    - reject self-directed edges;
    - deterministically order edges;
    - construct TransitionTopology;
    - construct TopologyProvenance.

    Prohibited:
    - runtime execution;
    - movement qualification;
    - momentum evaluation;
    - reverse-edge inference;
    - implicit edge generation;
    - post-compilation mutation.
    """

    VERSION = "topology-compiler-1.0.0"

    AUTHORIZED_RELATIONSHIP_TYPES = {
        "DIRECT_MOVEMENT_ELIGIBILITY",
    }

    VALID_EDGE_STATUSES = {
        "RATIFIED",
        "DEPRECATED",
    }

    @classmethod
    def compile(
        cls,
        *,
        topology_id: str,
        topology_version: str,
        topology_declaration_id: str,
        topology_declaration_version: str,
        topology_declaration_digest: str,
        basin_registry_id: str,
        basin_registry_digest: str,
        basin_ids: Iterable[str],
        edge_declarations: Sequence[
            DirectedTransitionEdge
        ],
        compiler_digest: str,
    ) -> tuple[
        TransitionTopology,
        TopologyProvenance,
    ]:
        basin_id_set = set(basin_ids)

        if not basin_id_set:
            raise TopologyCompilationError(
                "Ratified basin registry is empty."
            )

        if len(basin_id_set) != len(tuple(basin_ids)):
            raise TopologyCompilationError(
                "Ratified basin registry contains duplicate basin identities."
            )

        seen_edge_ids: set[str] = set()
        seen_relationships: set[
            tuple[str, str, str]
        ] = set()

        validated_edges: list[
            DirectedTransitionEdge
        ] = []

        for edge in edge_declarations:
            if edge.edge_id in seen_edge_ids:
                raise TopologyCompilationError(
                    f"Duplicate edge_id: {edge.edge_id}"
                )

            seen_edge_ids.add(edge.edge_id)

            if edge.source_basin not in basin_id_set:
                raise TopologyCompilationError(
                    "Unknown source basin: "
                    f"{edge.source_basin}"
                )

            if edge.target_basin not in basin_id_set:
                raise TopologyCompilationError(
                    "Unknown target basin: "
                    f"{edge.target_basin}"
                )

            if edge.source_basin == edge.target_basin:
                raise TopologyCompilationError(
                    "Self-directed edge is prohibited: "
                    f"{edge.edge_id}"
                )

            if (
                edge.relationship_type
                not in cls.AUTHORIZED_RELATIONSHIP_TYPES
            ):
                raise TopologyCompilationError(
                    "Unauthorized relationship type: "
                    f"{edge.relationship_type}"
                )

            if edge.status not in cls.VALID_EDGE_STATUSES:
                raise TopologyCompilationError(
                    "Invalid edge status: "
                    f"{edge.status}"
                )

            relationship_key = (
                edge.source_basin,
                edge.target_basin,
                edge.relationship_type,
            )

            if relationship_key in seen_relationships:
                raise TopologyCompilationError(
                    "Duplicate directed relationship: "
                    f"{edge.source_basin} -> "
                    f"{edge.target_basin} "
                    f"({edge.relationship_type})"
                )

            seen_relationships.add(
                relationship_key
            )

            validated_edges.append(edge)

        ordered_edges = tuple(
            sorted(
                validated_edges,
                key=lambda edge: (
                    edge.source_basin,
                    edge.target_basin,
                    edge.relationship_type,
                    edge.edge_id,
                ),
            )
        )

        authority = TopologyAuthorityMetadata(
            topology_declaration_id=(
                topology_declaration_id
            ),
            topology_declaration_version=(
                topology_declaration_version
            ),
            basin_registry_id=basin_registry_id,
            basin_registry_digest=(
                basin_registry_digest
            ),
            compiler_release=cls.VERSION,
            compiler_digest=compiler_digest,
        )

        topology_material = {
            "topology_id": topology_id,
            "topology_version": topology_version,
            "basin_registry_id": basin_registry_id,
            "basin_registry_digest": (
                basin_registry_digest
            ),
            "authority": asdict(authority),
            "directed_edges": [
                asdict(edge)
                for edge in ordered_edges
            ],
        }

        topology_digest = canonical_hash(
            topology_material
        )

        topology = TransitionTopology(
            topology_id=topology_id,
            topology_version=topology_version,
            topology_digest=topology_digest,
            basin_registry_id=basin_registry_id,
            basin_registry_digest=(
                basin_registry_digest
            ),
            authority=authority,
            directed_edges=ordered_edges,
        )

        provenance_material = {
            "topology_id": topology_id,
            "topology_digest": topology_digest,
            "declaration_refs": [
                topology_declaration_id,
            ],
            "edge_declaration_refs": sorted(
                edge.authority_ref
                for edge in ordered_edges
            ),
            "basin_registry_id": basin_registry_id,
            "basin_registry_digest": (
                basin_registry_digest
            ),
            "compiler_release": cls.VERSION,
            "compiler_digest": compiler_digest,
            "topology_declaration_digest": (
                topology_declaration_digest
            ),
        }

        provenance_id = (
            "TPROV-"
            + canonical_hash(
                provenance_material
            )[:16].upper()
        )

        provenance = TopologyProvenance(
            provenance_id=provenance_id,
            topology_id=topology_id,
            topology_digest=topology_digest,
            declaration_refs=(
                topology_declaration_id,
            ),
            edge_declaration_refs=tuple(
                sorted(
                    edge.authority_ref
                    for edge in ordered_edges
                )
            ),
            basin_registry_id=basin_registry_id,
            basin_registry_digest=(
                basin_registry_digest
            ),
            compiler_release=cls.VERSION,
            compiler_digest=compiler_digest,
        )

        return topology, provenance
