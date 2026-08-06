# REOS-TOPOLOGY-001 — Directed Transition Topology Governance

## Status

FROZEN

## Release

```text
v1.0.0-reos-topology-001
Horizon

Infrastructure

Purpose

REOS-TOPOLOGY-001 establishes the compiler-governed structural law required by the Movement Horizon.

It proves that directed basin connectivity can be:

declared independently of runtime execution;
compiled into an immutable TransitionTopology;
bound by deterministic identity and digest;
independently verified without runtime dependencies;
consumed later by movement contracts without allowing runtime topology invention.
Constitutional Actors
TopologyCompiler

Consumes:

ratified basin registry
ratified directed-edge declarations
topology declaration authority
compiler identity

Owns:

basin-reference validation
edge-authority validation
relationship-type validation
duplicate-edge rejection
self-loop rejection
deterministic edge ordering
topology identity construction
topology digest construction
topology provenance construction

Produces:

TransitionTopology
TopologyProvenance

Prohibited:

runtime execution
movement qualification
momentum evaluation
reverse-edge inference
implicit edge generation
post-compilation mutation
CleanRoomTopologyVerifier

Consumes:

TransitionTopology
TopologyProvenance

Owns:

digest-format verification
topology/provenance lineage verification
self-loop verification
duplicate-edge verification
relationship-type verification
edge-status verification
structured verification evidence

Produces:

TopologyVerificationReport

Prohibited:

topology construction
topology identity construction
edge generation
reverse-edge inference
artifact repair
artifact mutation
runtime execution
compiler execution
Constitutional Nouns
DirectedTransitionEdge
TopologyAuthorityMetadata
TransitionTopology
TopologyProvenance
TopologyVerificationCheck
TopologyVerificationReport
Proven Invariants
Directedness

Every edge is explicit and directed.

A → B

does not imply:

B → A

Reverse edges must be independently ratified and compiled.

Basin Integrity

Every source and target basin must exist in the supplied ratified basin registry.

Unknown basin identities fail closed.

Self-Loop Prohibition

Source and target basin identities must be distinct.

Self-directed edges are prohibited in this infrastructure baseline.

Duplicate-Edge Prohibition

Duplicate edge identifiers and duplicate directed relationships fail closed.

Relationship-Type Authority

REOS-TOPOLOGY-001 authorizes only:

DIRECT_MOVEMENT_ELIGIBILITY

Unknown or unratified relationship types fail closed.

Immutable Structural Truth

DirectedTransitionEdge and TransitionTopology are immutable data artifacts.

They contain no compiler, runtime, pathfinding, movement, or verification behavior.

Deterministic Compilation

Equivalent ratified basin and edge inputs produce identical:

TransitionTopology
TopologyProvenance
topology_digest
provenance_id

independent of edge input ordering.

Runtime Non-Ownership

Runtime components may consume only compiler-certified topology.

Runtime components may not:

invent topology
infer topology
modify topology
substitute topology
infer reverse edges
perform implicit path generation
Independent Verification

The clean-room verifier has zero runtime and compiler dependencies.

It emits structured verification checks and does not reconstruct or repair topology.

Foundation Services

The topology infrastructure uses the shared canonical identity layer for:

canonical_hash
is_valid_canonical_digest

Digest validation is framework-wide.

Topology verification report identity remains locally owned by the topology verifier.

Explicitly Out of Scope
runtime orientation
DirectionalCandidateGenerator
DirectionalCandidateSet
momentum evaluation
movement qualification
multi-hop traversal
pathfinding
SEAM interpretation
Shunt activation
Ontology handoff
RxREOS
remedy selection
protocol generation
PAR assembly
Artifact Inventory
spec/declarations/reos-topology-001.yaml

src/foundation/canonical.py
src/foundation/topology_types.py

src/compiler/topology_compiler.py

src/verifier/topology_verifier.py

tests/test_topology_nouns.py
tests/test_topology_verifier.py
tests/test_topology_compiler.py
Acceptance Evidence

At freeze:

123 tests collected
123 tests passed
Constitutional Dependency

This infrastructure milestone becomes a prerequisite for the Movement Horizon:

REOS-TOPOLOGY-001
        ↓
TransitionTopology
        ↓
REOS-004 TransitionContract
        ↓
DirectionalCandidateGenerator

REOS-004 may bind and consume the exact topology artifact by identity and digest.

REOS-004 does not own structural topology law.

Freeze Rule

REOS-TOPOLOGY-001 may be changed only to correct a demonstrated defect.

New relationship types, pathfinding, multi-hop traversal, topology mutation, movement execution, or domain-specific transition policies require later declarations.

Frozen topology actors may gain validation but may never gain jurisdiction.