"""Deterministic synthetic policy (fictional thresholds; not for clinical use)."""
from __future__ import annotations
from decimal import Decimal
from typing import Any
from contracts import Decision, RULE_ID, RULE_VERSION, POLICY, REFERENCE_TIME, SYSTEM_LOINC, HB_LOINC, ts

def decide(ctx: dict[str, Any]) -> Decision:
    """Fail-closed deterministic policy. No generative model on decision path."""
    f, w = ctx["facts"], ctx["workflow"]
    reasons: list[str] = []
    if not w["identity_verified"]:
        reasons.append("IDENTITY_NOT_VERIFIED")
    if not f["patient"] or f["encounter_patient"] != f["patient"] or f["observation_patient"] != f["patient"]:
        reasons.append("PATIENT_REFERENCE_CONFLICT")
    if not f["encounter"]:
        reasons.append("ENCOUNTER_MISSING")
    elif f["observation_encounter"] != f["encounter"]:
        reasons.append("ENCOUNTER_REFERENCE_CONFLICT")
    if f["age"] is None or isinstance(f["age"], bool) or not isinstance(f["age"], int) or f["age"] < 18:
        reasons.append("OUTSIDE_ADULT_TRAINING_SCOPE")
    if f["pregnant"] is not False:
        reasons.append("PREGNANCY_SCOPE_UNKNOWN_OR_EXCLUDED")
    if f["code_system"] != SYSTEM_LOINC or f["code"] != HB_LOINC:
        reasons.append("UNMAPPED_TEST_CODE")
    if f["status"] != "final":
        reasons.append("RESULT_NOT_FINAL")
    if f["hb_g_dl"] is None:
        reasons.append("UNUSABLE_HB_VALUE_OR_UNIT")
    observed = ts(f["when"])
    now = ts(REFERENCE_TIME)
    if observed is None:
        reasons.append("MISSING_OR_INVALID_TIME")
    elif observed > now:
        reasons.append("FUTURE_RESULT")
    elif (now - observed).total_seconds() > POLICY["fresh_days"] * 86400:
        reasons.append("STALE_RESULT")
    if reasons:
        return Decision("ABSTAIN", "BLOCKED", tuple(sorted(reasons)), RULE_ID, RULE_VERSION)
    hb = Decimal(f["hb_g_dl"])
    if hb < Decimal(POLICY["critical_below_g_dl"]):
        clinical = "URGENT_CLINICIAN_REVIEW"
    elif hb < Decimal(POLICY["review_below_g_dl"]):
        clinical = "CLINICIAN_REVIEW"
    else:
        clinical = "NO_TRAINING_THRESHOLD_ALERT"
    if w["consent_to_message"] and w["recipient"] and w["recipient"] == w["approved_recipient"]:
        communication = "ELIGIBLE_FOR_HUMAN_APPROVAL"
    else:
        communication = "BLOCKED"
        reasons.append("COMMUNICATION_NOT_AUTHORIZED")
    return Decision(clinical, communication, tuple(sorted(reasons)), RULE_ID, RULE_VERSION)


