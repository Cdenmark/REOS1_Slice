"""Governed noun authorization actor for REOS-004.

This module intentionally owns only the minimum production surface needed to
authorize governed noun representations into the frozen authorization nouns.
It does not mutate evidence, does not decide Binder jurisdiction, and does not
create any new authorization noun family.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, is_dataclass
from typing import Any, Final

from contracts.transition_contract import TransitionContract
from foundation.canonical import canonical_hash, is_valid_canonical_digest
from runtime.governed_noun_authorization import (
    GovernedNounAuthorizationEntry,
    GovernedNounAuthorizationEnvelope,
)
from runtime.recognition_result import RecognitionResult
from runtime.seam_aware_recognition_result import (
    SeamAwareRecognitionResult,
)
from verifier.vs003_clean_room_verifier import (
    VS003VerificationCheck,
    VS003VerificationReport,
)
from runtime.vs003_telemetry import VS003TransitionTelemetry


AUTHORIZATION_OPERATION: Final[str] = (
    "authorize_governed_noun_representation"
)

AUTHORIZATION_REASON_CODES: Final[frozenset[str]] = frozenset(
    {
        "AUTH_EVIDENCE_INVALID",
        "AUTH_CONTEXT_INVALID",
        "AUTH_REPRESENTATION_INVALID",
        "AUTH_VERIFICATION_INVALID",
        "AUTH_VERIFICATION_COVERAGE_INVALID",
        "AUTH_GOVERNED_NOUN_CORRESPONDENCE_INVALID",
        "AUTH_IDENTITY_COHERENCE_INVALID",
    }
)


class GovernedNounAuthorizationError(ValueError):
    """Fail-closed REOS-004 authorization error."""

    def __init__(self, reason_code: str, diagnostic: str) -> None:
        if reason_code not in AUTHORIZATION_REASON_CODES:
            raise ValueError(
                f"Unrecognized governed noun authorization reason code: {reason_code!r}"
            )

        super().__init__(f"[{reason_code}] {diagnostic}")
        self.reason_code = reason_code
        self.diagnostic = diagnostic


def _raise(reason_code: str, diagnostic: str) -> None:
    raise GovernedNounAuthorizationError(reason_code, diagnostic)


def _coerce_mapping(value: Any) -> Mapping[str, Any] | None:
    if value is None:
        return None

    if isinstance(value, Mapping):
        return value

    if is_dataclass(value):
        return asdict(value)

    if hasattr(value, "__dict__"):
        return {
            key: getattr(value, key)
            for key in vars(value)
            if not key.startswith("_")
        }

    return None


def _get_value(source: Any, *names: str) -> Any:
    mapping = _coerce_mapping(source)

    if mapping is not None:
        for name in names:
            if name in mapping:
                return mapping[name]

    for name in names:
        if hasattr(source, name):
            return getattr(source, name)

    return None


def _require_non_empty_string(value: Any, reason_code: str, diagnostic: str) -> str:
    if not isinstance(value, str) or not value:
        _raise(reason_code, diagnostic)

    return value


def _require_canonical_digest(value: Any, reason_code: str, diagnostic: str) -> str:
    if not is_valid_canonical_digest(value):
        _raise(reason_code, diagnostic)

    return value


def _extract_requested_artifacts(
    *,
    artifact: Any = None,
    artifacts: Any = None,
) -> tuple[Any, ...]:
    if artifact is not None and artifacts is not None:
        _raise(
            "AUTH_EVIDENCE_INVALID",
            "Supply either 'artifact' or 'artifacts', not both.",
        )

    if artifacts is not None:
        if isinstance(artifacts, tuple):
            return artifacts

        if isinstance(artifacts, list):
            return tuple(artifacts)

        return (artifacts,)

    if artifact is not None:
        return (artifact,)

    return ()


def _resolve_contract(contract: Any) -> TransitionContract:
    if not isinstance(contract, TransitionContract):
        _raise(
            "AUTH_EVIDENCE_INVALID",
            "A TransitionContract is required for governed noun authorization.",
        )

    return contract


def _validate_contract_context(contract: TransitionContract) -> str:
    try:
        contract_digest = contract.digest()
    except Exception as exc:  # pragma: no cover - defensive fail-closed
        _raise(
            "AUTH_CONTEXT_INVALID",
            f"TransitionContract digest recomputation failed: {exc}",
        )

    _require_canonical_digest(
        contract_digest,
        "AUTH_CONTEXT_INVALID",
        "TransitionContract digest is not a canonical digest.",
    )

    authority = contract.authority

    _require_non_empty_string(
        getattr(authority, "declaration_id", None),
        "AUTH_CONTEXT_INVALID",
        "TransitionContract authority declaration_id is missing.",
    )
    _require_canonical_digest(
        getattr(authority, "declaration_hash", None),
        "AUTH_CONTEXT_INVALID",
        "TransitionContract authority declaration_hash is malformed.",
    )
    _require_non_empty_string(
        getattr(authority, "compiler_release", None),
        "AUTH_CONTEXT_INVALID",
        "TransitionContract authority compiler_release is missing.",
    )
    _require_canonical_digest(
        getattr(authority, "compiler_digest", None),
        "AUTH_CONTEXT_INVALID",
        "TransitionContract authority compiler_digest is malformed.",
    )
    _require_non_empty_string(
        getattr(authority, "generated_at", None),
        "AUTH_CONTEXT_INVALID",
        "TransitionContract authority generated_at is missing.",
    )

    allowed_operations = getattr(contract, "allowed_operations", None)

    if not isinstance(allowed_operations, list):
        _raise(
            "AUTH_CONTEXT_INVALID",
            "TransitionContract allowed_operations must be a list.",
        )

    if AUTHORIZATION_OPERATION not in allowed_operations:
        _raise(
            "AUTH_CONTEXT_INVALID",
            "TransitionContract does not authorize governed noun representation.",
        )

    return contract_digest


def _require_policy(policy: Any) -> Mapping[str, Any] | None:
    resolved = _coerce_mapping(policy)

    if resolved is None:
        _raise(
            "AUTH_EVIDENCE_INVALID",
            "A governed noun mapping policy is required.",
        )

    return resolved


def _resolve_policy_binding(policy: Mapping[str, Any]) -> tuple[str, str]:
    declaration_id = policy.get("declaration_id")
    symbolic_name = policy.get("symbolic_name")

    if declaration_id is None and symbolic_name is None:
        governed_nouns = policy.get("governed_nouns")

        if isinstance(governed_nouns, Mapping):
            if len(governed_nouns) != 1:
                _raise(
                    "AUTH_GOVERNED_NOUN_CORRESPONDENCE_INVALID",
                    "The governed noun mapping policy must resolve one declared noun.",
                )

            declaration_key, noun_binding = next(iter(governed_nouns.items()))

            if isinstance(declaration_key, tuple) and len(declaration_key) == 2:
                declaration_id, symbolic_name = declaration_key
            elif isinstance(noun_binding, Mapping):
                declaration_id = noun_binding.get("declaration_id")
                symbolic_name = noun_binding.get("symbolic_name")
            elif isinstance(noun_binding, type):
                declaration_id = declaration_key
                symbolic_name = noun_binding.__name__

        elif len(policy) == 1:
            declaration_key, noun_binding = next(iter(policy.items()))

            if isinstance(declaration_key, tuple) and len(declaration_key) == 2:
                declaration_id, symbolic_name = declaration_key
            elif isinstance(noun_binding, Mapping):
                declaration_id = noun_binding.get("declaration_id")
                symbolic_name = noun_binding.get("symbolic_name")

    declaration_id = _require_non_empty_string(
        declaration_id,
        "AUTH_GOVERNED_NOUN_CORRESPONDENCE_INVALID",
        "The governed noun mapping policy does not declare a declaration_id.",
    )
    symbolic_name = _require_non_empty_string(
        symbolic_name,
        "AUTH_GOVERNED_NOUN_CORRESPONDENCE_INVALID",
        "The governed noun mapping policy does not declare a symbolic noun name.",
    )

    if declaration_id != "REOS-004" or symbolic_name != "SeamAwareRecognitionResult":
        _raise(
            "AUTH_GOVERNED_NOUN_CORRESPONDENCE_INVALID",
            "The governed noun mapping policy does not authorize SeamAwareRecognitionResult under REOS-004.",
        )

    return declaration_id, symbolic_name


def _resolve_shared_policy(policy: Any) -> Mapping[str, Any]:
    return _require_policy(policy)


def _resolve_report(report: Any) -> VS003VerificationReport:
    if not isinstance(report, VS003VerificationReport):
        _raise(
            "AUTH_EVIDENCE_INVALID",
            "A VS003VerificationReport is required for authorization.",
        )

    return report


def _resolve_telemetry(telemetry: Any) -> VS003TransitionTelemetry:
    if not isinstance(telemetry, VS003TransitionTelemetry):
        _raise(
            "AUTH_EVIDENCE_INVALID",
            "A VS003TransitionTelemetry companion evidence object is required.",
        )

    return telemetry


def _validate_verification_report(report: VS003VerificationReport) -> str:
    _require_non_empty_string(
        getattr(report, "report_id", None),
        "AUTH_EVIDENCE_INVALID",
        "Verification report identity is missing.",
    )

    if not isinstance(report.verified, bool):
        _raise(
            "AUTH_VERIFICATION_INVALID",
            "Verification report verified state must be boolean.",
        )

    if not report.verified:
        _raise(
            "AUTH_VERIFICATION_INVALID",
            "Verification report is not successful.",
        )

    if not isinstance(report.checks, tuple):
        _raise(
            "AUTH_VERIFICATION_INVALID",
            "Verification report checks must be a tuple.",
        )

    if not report.checks:
        _raise(
            "AUTH_VERIFICATION_INVALID",
            "Verification report does not contain any verification checks.",
        )

    for check in report.checks:
        if not isinstance(check, VS003VerificationCheck):
            _raise(
                "AUTH_VERIFICATION_INVALID",
                "Verification report contains a malformed verification check.",
            )

        if not check.passed:
            _raise(
                "AUTH_VERIFICATION_INVALID",
                "Verification report contains a failed verification check.",
            )

    report_digest = canonical_hash(asdict(report))
    _require_canonical_digest(
        report_digest,
        "AUTH_VERIFICATION_INVALID",
        "Verification report digest could not be derived.",
    )

    return report_digest


def _validate_artifact_representation(
    artifact: SeamAwareRecognitionResult,
    telemetry: VS003TransitionTelemetry,
) -> str:
    if type(artifact) is not SeamAwareRecognitionResult:
        _raise(
            "AUTH_GOVERNED_NOUN_CORRESPONDENCE_INVALID",
            "Structural lookalike substitution is not authorized for SeamAwareRecognitionResult.",
        )

    if not isinstance(artifact.base_result, RecognitionResult):
        _raise(
            "AUTH_REPRESENTATION_INVALID",
            "SeamAwareRecognitionResult base_result is malformed.",
        )

    if artifact.base_result.orientation.primary_basin != artifact.primary_basin:
        _raise(
            "AUTH_REPRESENTATION_INVALID",
            "SeamAwareRecognitionResult primary basin does not match its base result.",
        )

    if artifact.base_result.recognition_unit_id != telemetry.recognition_unit_id:
        _raise(
            "AUTH_REPRESENTATION_INVALID",
            "SeamAwareRecognitionResult recognition unit lineage does not match the companion evidence.",
        )

    if artifact.orientation_resolution_id != telemetry.orientation_resolution_id:
        _raise(
            "AUTH_REPRESENTATION_INVALID",
            "SeamAwareRecognitionResult orientation resolution lineage does not match the companion evidence.",
        )

    if artifact.result_id != telemetry.result_id:
        _raise(
            "AUTH_REPRESENTATION_INVALID",
            "SeamAwareRecognitionResult identity does not match the companion evidence.",
        )

    artifact_digest = canonical_hash(asdict(artifact))

    if artifact_digest != telemetry.result_digest:
        _raise(
            "AUTH_REPRESENTATION_INVALID",
            "SeamAwareRecognitionResult canonical digest does not match the companion commitment.",
        )

    return artifact_digest


def _validate_exact_coverage(
    artifact: SeamAwareRecognitionResult,
    report: VS003VerificationReport,
    telemetry: VS003TransitionTelemetry,
    artifact_digest: str,
) -> None:
    if report.orientation_resolution_id != artifact.orientation_resolution_id:
        _raise(
            "AUTH_VERIFICATION_COVERAGE_INVALID",
            "Verification report does not identify the authorized SeamAwareRecognitionResult orientation resolution.",
        )

    if telemetry.orientation_resolution_id != artifact.orientation_resolution_id:
        _raise(
            "AUTH_VERIFICATION_COVERAGE_INVALID",
            "Companion evidence does not identify the authorized SeamAwareRecognitionResult orientation resolution.",
        )

    if telemetry.result_id != artifact.result_id:
        _raise(
            "AUTH_VERIFICATION_COVERAGE_INVALID",
            "Companion evidence does not identify the authorized SeamAwareRecognitionResult identity.",
        )

    if telemetry.recognition_unit_id != artifact.base_result.recognition_unit_id:
        _raise(
            "AUTH_VERIFICATION_COVERAGE_INVALID",
            "Companion evidence does not preserve the SeamAwareRecognitionResult recognition unit lineage.",
        )

    if artifact.base_result.orientation.primary_basin != artifact.primary_basin:
        _raise(
            "AUTH_VERIFICATION_COVERAGE_INVALID",
            "The SeamAwareRecognitionResult base result does not preserve the selected primary basin.",
        )

    if telemetry.result_digest != artifact_digest:
        _raise(
            "AUTH_VERIFICATION_COVERAGE_INVALID",
            "Companion evidence canonical commitment does not equal the recomputed SeamAwareRecognitionResult digest.",
        )

    if artifact.active_seam is None and artifact.resolution_state != "ORIENTED":
        _raise(
            "AUTH_VERIFICATION_COVERAGE_INVALID",
            "SeamAwareRecognitionResult resolution state is not coherent with the absence of an active seam.",
        )

    if artifact.active_seam is not None and artifact.resolution_state != "SEAM_ACTIVE":
        _raise(
            "AUTH_VERIFICATION_COVERAGE_INVALID",
            "SeamAwareRecognitionResult resolution state is not coherent with the presence of an active seam.",
        )


def _build_entry(
    artifact: SeamAwareRecognitionResult,
    report: VS003VerificationReport,
    contract_digest: str,
    declaration_id: str,
    symbolic_name: str,
) -> GovernedNounAuthorizationEntry:
    artifact_digest = canonical_hash(asdict(artifact))
    report_digest = canonical_hash(asdict(report))

    authorization_material = {
        "artifact_ref": artifact.result_id,
        "artifact_digest": artifact_digest,
        "governed_noun_declaration_id": declaration_id,
        "governed_noun_symbolic_name": symbolic_name,
        "verification_report_id": report.report_id,
        "verification_report_digest": report_digest,
        "authority_context_digest": contract_digest,
    }

    return GovernedNounAuthorizationEntry(
        artifact_ref=artifact.result_id,
        artifact_digest=artifact_digest,
        governed_noun_declaration_id=declaration_id,
        governed_noun_symbolic_name=symbolic_name,
        verification_report_id=report.report_id,
        verification_report_digest=report_digest,
        authorization_digest=canonical_hash(authorization_material),
    )


def _build_envelope(
    entries: tuple[GovernedNounAuthorizationEntry, ...],
    contract: TransitionContract,
) -> GovernedNounAuthorizationEnvelope:
    contract_digest = contract.digest()
    ordered_entries = tuple(
        sorted(
            entries,
            key=lambda entry: (
                entry.authorization_digest,
                entry.artifact_ref,
            ),
        )
    )

    envelope_material = {
        "transition_contract_ref": contract.contract_id,
        "contract_digest": contract_digest,
        "authorization_entry_digests": [
            entry.authorization_digest for entry in ordered_entries
        ],
    }

    return GovernedNounAuthorizationEnvelope(
        transition_contract_ref=contract.contract_id,
        contract_digest=contract_digest,
        authorization_entries=ordered_entries,
        envelope_digest=canonical_hash(envelope_material),
    )


class GovernedNounAuthorizationAdjudicator:
    """Stateless adjudicator for governed noun authorization."""

    def adjudicate(
        self,
        *,
        artifact: Any = None,
        artifacts: Any = None,
        verification_report: Any,
        companion_evidence: Any,
        contract: Any,
        governed_noun_mapping_policy: Any,
    ) -> GovernedNounAuthorizationEnvelope:
        artifacts = _extract_requested_artifacts(
            artifact=artifact,
            artifacts=artifacts,
        )

        if not artifacts:
            _raise(
                "AUTH_EVIDENCE_INVALID",
                "At least one artifact representation is required.",
            )

        contract = _resolve_contract(contract)
        contract_digest = _validate_contract_context(contract)
        policy = _resolve_shared_policy(governed_noun_mapping_policy)
        declaration_id, symbolic_name = _resolve_policy_binding(policy)

        report = _resolve_report(verification_report)
        telemetry = _resolve_telemetry(companion_evidence)
        report_digest = _validate_verification_report(report)

        if not is_valid_canonical_digest(report_digest):
            _raise(
                "AUTH_VERIFICATION_INVALID",
                "Verification report digest is malformed.",
            )

        entries: list[GovernedNounAuthorizationEntry] = []
        seen_authorization_digests: set[str] = set()

        for artifact in artifacts:
            if not isinstance(artifact, SeamAwareRecognitionResult):
                _raise(
                    "AUTH_GOVERNED_NOUN_CORRESPONDENCE_INVALID",
                    "Only SeamAwareRecognitionResult artifacts are authorized by this actor.",
                )

            artifact_digest = _validate_artifact_representation(
                artifact,
                telemetry,
            )

            _validate_exact_coverage(
                artifact,
                report,
                telemetry,
                artifact_digest,
            )

            entry = _build_entry(
                artifact=artifact,
                report=report,
                contract_digest=contract_digest,
                declaration_id=declaration_id,
                symbolic_name=symbolic_name,
            )

            if entry.authorization_digest in seen_authorization_digests:
                _raise(
                    "AUTH_IDENTITY_COHERENCE_INVALID",
                    "Duplicate authorization_digest values are not allowed within one authorization envelope.",
                )

            seen_authorization_digests.add(entry.authorization_digest)
            entries.append(entry)

        try:
            return _build_envelope(tuple(entries), contract)
        except ValueError as exc:
            _raise(
                "AUTH_IDENTITY_COHERENCE_INVALID",
                str(exc),
            )
