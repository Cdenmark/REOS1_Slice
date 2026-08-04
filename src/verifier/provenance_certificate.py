import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Tuple

from verifier.artifact_registration import ArtifactRegistration
from verifier.verification_report import IndependentVerificationReport


@dataclass(frozen=True)
class ProvenanceLink:
    """One directed link in the certified execution lineage."""

    source_artifact_id: str
    target_artifact_id: str
    relationship: str


@dataclass(frozen=True)
class ProvenanceCertificate:
    """
    Immutable certificate for one constitutionally closed execution.

    The certificate records and binds the completed lineage.
    It does not alter any registered artifact.
    """

    certificate_id: str
    transition_id: str
    registration_id: str
    verification_report_id: str
    links: Tuple[ProvenanceLink, ...]
    status: str = "CERTIFIED"


def _canonical_hash(data: object) -> str:
    serialized = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")

    return hashlib.sha256(serialized).hexdigest()


def certify_provenance(
    registration: ArtifactRegistration,
    report: IndependentVerificationReport,
) -> ProvenanceCertificate:
    """
    Certify the lineage of one registered and independently verified run.

    Certification fails closed when registration and verification disagree.
    """
    if not report.verified:
        raise ValueError(
            "A failed verification report cannot receive provenance certification."
        )

    if registration.transition_id != report.transition_id:
        raise ValueError(
            "Registration and verification transition identities do not match."
        )

    if registration.verification_report_id != report.report_id:
        raise ValueError(
            "Registration does not reference the supplied verification report."
        )

    artifact_ids = {
        artifact.artifact_type: artifact.artifact_id
        for artifact in registration.artifacts
    }

    required_artifacts = {
        "recognition_result",
        "transition_telemetry",
        "independent_verification_report",
    }

    if set(artifact_ids) != required_artifacts:
        raise ValueError(
            "Registration does not contain the complete VS001 artifact set."
        )

    links = (
        ProvenanceLink(
            source_artifact_id=report.transition_id,
            target_artifact_id=artifact_ids["recognition_result"],
            relationship="produced_recognition_result",
        ),
        ProvenanceLink(
            source_artifact_id=report.transition_id,
            target_artifact_id=artifact_ids["transition_telemetry"],
            relationship="produced_transition_telemetry",
        ),
        ProvenanceLink(
            source_artifact_id=artifact_ids["recognition_result"],
            target_artifact_id=report.report_id,
            relationship="independently_verified_by",
        ),
        ProvenanceLink(
            source_artifact_id=artifact_ids["transition_telemetry"],
            target_artifact_id=report.report_id,
            relationship="independently_verified_by",
        ),
        ProvenanceLink(
            source_artifact_id=report.report_id,
            target_artifact_id=registration.registration_id,
            relationship="admitted_by_registration",
        ),
    )

    certificate_material = {
        "transition_id": report.transition_id,
        "registration_id": registration.registration_id,
        "verification_report_id": report.report_id,
        "links": [asdict(link) for link in links],
        "status": "CERTIFIED",
    }

    return ProvenanceCertificate(
        certificate_id=(
            "PC-"
            + _canonical_hash(certificate_material)[:16].upper()
        ),
        transition_id=report.transition_id,
        registration_id=registration.registration_id,
        verification_report_id=report.report_id,
        links=links,
    )
