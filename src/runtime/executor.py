from dataclasses import dataclass
from typing import Callable, Dict

from contracts.transition_contract import TransitionContract


class ConstitutionalViolationError(Exception):
    """Raised when runtime execution exceeds contract authority."""


Operation = Callable[[], object]


@dataclass
class OperationExecutor:
    """
    Passive operation executor.

    The executor knows operational capabilities only.
    It has no knowledge of governance rules or doctrine identifiers.
    """

    operations: Dict[str, Operation]

    def execute_operation(
        self,
        contract: TransitionContract,
        operation_name: str,
    ) -> object:
        if operation_name not in contract.allowed_operations:
            raise ConstitutionalViolationError(
                f"Unauthorized operation: '{operation_name}' "
                f"is not permitted by contract '{contract.contract_id}'."
            )

        operation = self.operations.get(operation_name)

        if operation is None:
            raise ConstitutionalViolationError(
                f"Unavailable operation: '{operation_name}' "
                "has no registered runtime implementation."
            )

        return operation()
