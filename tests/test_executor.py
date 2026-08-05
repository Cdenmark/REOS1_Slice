import pytest

from contracts.transition_contract import (
    AuthorityMetadata,
    TransitionContract,
)
from runtime.executor import (
    ConstitutionalViolationError,
    OperationExecutor,
)


def make_contract(allowed_operations: list[str]) -> TransitionContract:
    return TransitionContract(
        contract_id="CONTRACT-REOS-001",
        transition_id="REOS-001",
        authority=AuthorityMetadata(
            declaration_id="REOS-001",
            declaration_hash="a" * 64,
            compiler_release="compiler-0.1.0",
            compiler_digest="b" * 64,
            generated_at="2026-08-04T18:00:00+00:00",
        ),
        constitution_version="2.0.0",
        contract_version="1.0.0",
        allowed_operations=allowed_operations,
        permitted_exports=[],
        prohibited_exports=[],
        operation_parameters={},
    )


def test_executor_runs_authorized_operation():
    executor = OperationExecutor(
        operations={
            "ingress_hash": lambda: "executed",
        }
    )

    result = executor.execute_operation(
        contract=make_contract(["ingress_hash"]),
        operation_name="ingress_hash",
    )

    assert result == "executed"


def test_executor_rejects_unauthorized_operation():
    executor = OperationExecutor(
        operations={
            "ingress_hash": lambda: "executed",
        }
    )

    with pytest.raises(
        ConstitutionalViolationError,
        match="Unauthorized operation",
    ):
        executor.execute_operation(
            contract=make_contract([]),
            operation_name="ingress_hash",
        )


def test_executor_rejects_unavailable_operation():
    executor = OperationExecutor(operations={})

    with pytest.raises(
        ConstitutionalViolationError,
        match="Unavailable operation",
    ):
        executor.execute_operation(
            contract=make_contract(["ingress_hash"]),
            operation_name="ingress_hash",
        )
