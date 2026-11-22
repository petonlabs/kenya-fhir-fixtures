"""Compare decision-relevant evidence and authorization, not just outcome labels."""
from __future__ import annotations
from datetime import timezone
from typing import Any
from contracts import Decision, ts

EVIDENCE_FIELDS = (
    "patient", "encounter_patient", "observation_patient",
    "encounter", "observation_encounter", "code_system", "code",
    "hb_g_dl", "status", "age", "pregnant",
)
WORKFLOW_FIELDS = (
    "identity_verified", "consent_to_message", "recipient", "approved_recipient",
)


def evidence_signature(context: dict[str, Any]) -> tuple[Any, ...]:
    """Compare instant and canonical value; exclude raw unit and source-local IDs."""
    facts = context["facts"]
    stamp = ts(facts.get("when"))
    instant = stamp.astimezone(timezone.utc).isoformat() if stamp else None
    return (
        *(facts.get(field) for field in EVIDENCE_FIELDS),
        instant,
        tuple(context.get("adapter_issues", [])),
    )


def compare(a: dict[str, Any], b: dict[str, Any], da: Decision, db: Decision) -> dict[str, Any]:
    axes = {
        "evidence": evidence_signature(a) == evidence_signature(b),
        "clinical_decision": da.clinical == db.clinical,
        "communication_authorization": da.communication == db.communication,
        "reason_codes": da.reasons == db.reasons,
        "workflow_context": all(
            a["workflow"].get(field) == b["workflow"].get(field)
            for field in WORKFLOW_FIELDS
        ),
        "rule_identity": (da.rule, da.rule_version) == (db.rule, db.rule_version),
    }
    return {"axes": axes, "equivalent": all(axes.values()),
            "discrepancy_axes": sorted(k for k, v in axes.items() if not v)}
