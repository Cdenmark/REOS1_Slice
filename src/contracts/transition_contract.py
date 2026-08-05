from dataclasses import dataclass
from typing import Any, Dict, List

from runtime.serializer import canonical_hash


@dataclass(frozen=True)
class AuthorityMetadata:
    """
    Compiler-issued authority metadata.

    This object identifies the ratified declaration and compiler
    artifact that authorized the TransitionContract.
    """

    declaration_id: str
    declaration_hash: str
    compiler_release: str
    compiler_digest: str
    generated_at: str


@dataclass(frozen=True)
class TransitionContract:
    """
    Immutable compiler-issued execution mandate.

    The contract authorizes runtime operations and carries all
    compiler-issued parameters required by those operations.

    The runtime may consume these parameters.
    It may not invent, default, or modify them.
    """

    contract_id: str
    transition_id: str
    authority: AuthorityMetadata

    constitution_version: str
    contract_version: str

    allowed_operations: List[str]
    permitted_exports: List[str]
    prohibited_exports: List[str]

    operation_parameters: Dict[str, Dict[str, Any]]

    def digest(self) -> str:
        """
        Return a deterministic digest of the complete authority mandate.

        Authorization-list order is normalized because membership,
        not authoring order, defines the contract.

        Operation parameters remain structurally canonicalized by
        canonical_hash.
        """
        return canonical_hash(
            {
                "contract_id": self.contract_id,
                "transition_id": self.transition_id,
                "authority": {
                    "declaration_id": self.authority.declaration_id,
                    "declaration_hash": self.authority.declaration_hash,
                    "compiler_release": self.authority.compiler_release,
                    "compiler_digest": self.authority.compiler_digest,
                    "generated_at": self.authority.generated_at,
                },
                "constitution_version": self.constitution_version,
                "contract_version": self.contract_version,
                "allowed_operations": sorted(
                    self.allowed_operations
                ),
                "permitted_exports": sorted(
                    self.permitted_exports
                ),
                "prohibited_exports": sorted(
                    self.prohibited_exports
                ),
                "operation_parameters": self.operation_parameters,
            }
        )
