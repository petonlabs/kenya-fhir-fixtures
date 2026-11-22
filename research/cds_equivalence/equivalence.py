#!/usr/bin/env python3
"""Independent synthetic cross-HMIS clinical-decision equivalence experiment.

No source code or rule text is copied from the CHUNGUZA workshop.
The deliberately fictional policy is NOT approved for patient care.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

RULE_ID = "petonlabs.synthetic.hb-review"
RULE_VERSION = "0.1.0-training-only"
MAPPING_VERSION = "0.1.0"
REFERENCE_TIME = "2026-11-22T12:00:00+03:00"
POLICY = {"rule": RULE_ID, "version": RULE_VERSION, "critical_below_g_dl": "7", "review_below_g_dl": "10", "fresh_days": 30, "adult_min_age": 18}
SYSTEM_LOINC = "http://loinc.org"
HB_LOINC = "718-7"
SCHEMA_VERSION = "0.1.0"


def digest(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def ts(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return moment if moment.tzinfo else None
    except ValueError:
        return None


def fhir_ref(reference: Any, prefix: str) -> str | None:
    if not isinstance(reference, str) or not reference.startswith(prefix + "/"):
        return None
    suffix = reference[len(prefix) + 1:]
    return suffix if suffix and "/" not in suffix and "?" not in suffix else None


def normalize_hb(value: Any, unit: Any) -> str | None:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return None
    try:
        v = Decimal(str(value))
    except InvalidOperation:
        return None
    if not v.is_finite() or not 0 < v < 300:
        return None
    if unit == "g/dL":
        v_gdl = v
    elif unit == "g/L":
        v_gdl = v / Decimal(10)
    else:
        return None
    if not 0 < v_gdl < 30:
        return None
    return str(v_gdl.normalize())


def canonical(source: str, record: dict[str, Any]) -> dict[str, Any]:
    """Adapt two dissimilar inputs into the same minimal typed decision contract."""
    workflow = record["workflow"]
    if source == "fhir":
        entries = record["bundle"]["entry"]
        resources = {e["resource"]["resourceType"]: e["resource"] for e in entries}
        p, e, o = (resources[t] for t in ("Patient", "Encounter", "Observation"))
        coding = o.get("code", {}).get("coding", [{}])[0]
        q = o.get("valueQuantity", {})
        raw = {
            "patient": p.get("id"), "encounter_patient": fhir_ref(e.get("subject", {}).get("reference"), "Patient"),
            "observation_patient": fhir_ref(o.get("subject", {}).get("reference"), "Patient"),
            "status": o.get("status"), "code_system": coding.get("system"), "code": coding.get("code"),
            "value": q.get("value"), "unit": q.get("code"), "when": o.get("effectiveDateTime"),
            "observation_id": "Observation/" + str(o.get("id", "unknown")), "encounter": e.get("id"),
            "observation_encounter": fhir_ref(o.get("encounter", {}).get("reference"), "Encounter"),
            "age": workflow.get("age_years"), "pregnant": workflow.get("pregnant"),
        }
    elif source == "legacy":
        p, e, lab = (record[t] for t in ("patient", "visit", "lab"))
        statuses = {"released": "final", "draft": "preliminary", "corrected": "amended"}
        codes = {"HB": (SYSTEM_LOINC, HB_LOINC), "HGB": (SYSTEM_LOINC, HB_LOINC)}
        system, code = codes.get(lab.get("test"), (None, None))
        raw = {
            "patient": p.get("key"), "encounter_patient": e.get("patient_key"),
            "observation_patient": lab.get("patient_key"), "status": statuses.get(lab.get("state")),
            "code_system": system, "code": code, "value": lab.get("number"), "unit": lab.get("uom"),
            "when": lab.get("collected_at"), "observation_id": "legacy-lab/" + str(lab.get("key", "unknown")),
            "encounter": e.get("key"), "observation_encounter": lab.get("visit_key"), "age": workflow.get("age_years"), "pregnant": workflow.get("pregnant"),
        }
    else:
        raise ValueError("Unsupported adapter")
    return {
        "facts": {**raw, "hb_g_dl": normalize_hb(raw["value"], raw["unit"])},
        "workflow": {
            "identity_verified": workflow.get("identity_verified") is True,
            "consent_to_message": workflow.get("consent_to_message") is True,
            "recipient": workflow.get("recipient"), "approved_recipient": workflow.get("approved_recipient"),
        },
        "provenance": {"adapter": source, "mapping_version": MAPPING_VERSION,
                       "source_hash_sha256": digest(record), "source_ref": raw["observation_id"]},
    }


@dataclass(frozen=True)
class Decision:
    clinical: str
    communication: str
    reasons: tuple[str, ...]
    rule: str
    rule_version: str


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


def base_pair() -> tuple[dict[str, Any], dict[str, Any]]:
    wf = {"identity_verified": True, "consent_to_message": True, "recipient": "+254700000000",
          "approved_recipient": "+254700000000", "age_years": 35, "pregnant": False}
    fhir = {"bundle": {"resourceType": "Bundle", "type": "collection", "entry": [
        {"resource": {"resourceType": "Patient", "id": "pat-101", "identifier": [{"system": "https://example.org/synthetic-id", "value": "FAKE-101"}]}},
        {"resource": {"resourceType": "Encounter", "id": "enc-101", "status": "in-progress", "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB"}, "subject": {"reference": "Patient/pat-101"}}},
        {"resource": {"resourceType": "Observation", "id": "obs-101", "status": "final", "code": {"coding": [{"system": SYSTEM_LOINC, "code": HB_LOINC}]}, "subject": {"reference": "Patient/pat-101"}, "encounter": {"reference": "Encounter/enc-101"}, "effectiveDateTime": "2026-11-20T08:30:00+03:00", "valueQuantity": {"value": 6.8, "unit": "g/dL", "system": "http://unitsofmeasure.org", "code": "g/dL"}}}
    ]}, "workflow": copy.deepcopy(wf)}
    legacy = {"patient": {"key": "pat-101"}, "visit": {"key": "enc-101", "patient_key": "pat-101"},
              "lab": {"key": "lb-101", "patient_key": "pat-101", "visit_key": "enc-101", "state": "released", "test": "HB", "number": "6.8", "uom": "g/dL", "collected_at": "2026-11-20T08:30:00+03:00"}, "workflow": copy.deepcopy(wf)}
    return fhir, legacy


def scenarios() -> list[dict[str, Any]]:
    """Four equivalent controls, eight deliberate safety/semantics drifts."""
    specs = [
        ("01-critical-equivalent", "same", "critical final result", lambda a, b: None),
        ("02-normal-equivalent", "same", "normal-range training result", lambda a, b: (a["bundle"]["entry"][2]["resource"]["valueQuantity"].update(value=12.1), b["lab"].update(number="12.1"))),
        ("03-unit-equivalent", "same", "legacy g/L normalized to g/dL", lambda a, b: b["lab"].update(number="68", uom="g/L")),
        ("04-preliminary-equivalent", "same", "both abstain on nonfinal result", lambda a, b: (a["bundle"]["entry"][2]["resource"].update(status="preliminary"), b["lab"].update(state="draft"))),
        ("05-wrong-patient", "different", "legacy observation linked to a different patient", lambda a, b: b["lab"].update(patient_key="pat-999")),
        ("06-stale", "different", "legacy result is outside recency window", lambda a, b: b["lab"].update(collected_at="2026-08-10T08:30:00+03:00")),
        ("07-premature-status", "different", "legacy result still draft", lambda a, b: b["lab"].update(state="draft")),
        ("08-unknown-unit", "different", "legacy unit cannot be converted safely", lambda a, b: b["lab"].update(uom="unknown")),
        ("09-future-result", "different", "legacy timestamp is in the future", lambda a, b: b["lab"].update(collected_at="2026-12-01T08:30:00+03:00")),
        ("10-unmapped-test", "different", "legacy local code cannot be reliably mapped", lambda a, b: b["lab"].update(test="BLOOD")),
        ("11-no-message-consent", "different", "clinical decision agrees but disclosure authorization differs", lambda a, b: b["workflow"].update(consent_to_message=False)),
        ("12-identity-unverified", "different", "legacy-side patient choice lacks explicit confirmation", lambda a, b: b["workflow"].update(identity_verified=False)),
    ]
    result = []
    for ident, expected, description, mutate in specs:
        a, b = base_pair()
        mutate(a, b)
        result.append({"id": ident, "description": description, "expected": expected, "fhir": a, "legacy": b})
    return result


def local_fhir_shape_check(bundle: dict[str, Any]) -> list[str]:
    """Narrow local check ONLY; never presented as HL7 or Kenya Core validation."""
    problems: list[str] = []
    if bundle.get("resourceType") != "Bundle" or bundle.get("type") != "collection":
        problems.append("BUNDLE_SHAPE")
    rows = bundle.get("entry")
    if not isinstance(rows, list):
        return problems + ["ENTRIES_MISSING"]
    kinds = [v.get("resource", {}).get("resourceType") for v in rows if isinstance(v, dict)]
    for expected in ("Patient", "Encounter", "Observation"):
        if kinds.count(expected) != 1:
            problems.append("RESOURCE_COUNT_" + expected.upper())
    return problems


def run() -> dict[str, Any]:
    records = []
    for case in scenarios():
        shape = local_fhir_shape_check(case["fhir"]["bundle"])
        fhir_ctx = canonical("fhir", case["fhir"])
        legacy_ctx = canonical("legacy", case["legacy"])
        fhir_dec = decide(fhir_ctx)
        legacy_dec = decide(legacy_ctx)
        equivalent = (fhir_dec.clinical, fhir_dec.communication, fhir_dec.reasons) == (legacy_dec.clinical, legacy_dec.communication, legacy_dec.reasons)
        expected_same = case["expected"] == "same"
        records.append({
            "case_id": case["id"], "description": case["description"], "expected_relation": case["expected"],
            "observed_equivalent": equivalent, "detector_matched_expected": equivalent == expected_same,
            "local_fhir_shape_errors": shape, "fhir": {"canonical": fhir_ctx, "decision": asdict(fhir_dec)},
            "legacy": {"canonical": legacy_ctx, "decision": asdict(legacy_dec)},
            "audit_hash_sha256": digest({"case": case["id"], "fhir": fhir_ctx, "legacy": legacy_ctx, "fhir_decision": asdict(fhir_dec), "legacy_decision": asdict(legacy_dec)})
        })
    matched = sum(r["detector_matched_expected"] for r in records)
    detected = sum(r["expected_relation"] == "different" and not r["observed_equivalent"] for r in records)
    return {"schema_version": SCHEMA_VERSION, "title": "Synthetic cross-HMIS CDS equivalence experiment",
            "clinical_validation": "NOT_PERFORMED", "kenya_core_ig_validation": "NOT_PERFORMED_FOR_NEW_CASES",
            "policy": POLICY, "policy_hash_sha256": digest(POLICY), "mapping_version": MAPPING_VERSION,
            "reference_time": REFERENCE_TIME, "source_systems": ["FHIR_R4_SYNTHETIC", "LEGACY_SQL_SHAPE_SYNTHETIC"],
            "summary": {"total": len(records), "expected_equivalent": sum(r["expected_relation"] == "same" for r in records),
                        "expected_drift": sum(r["expected_relation"] == "different" for r in records),
                        "drifts_detected": detected, "expectations_matched": matched, "all_expectations_met": matched == len(records)},
            "cases": records}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report", type=Path, default=Path("reports/equivalence.json"))
    args = p.parse_args()
    result = run()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    s = result["summary"]
    print(f"{s['expectations_matched']}/{s['total']} expected outcomes matched; {s['drifts_detected']}/{s['expected_drift']} intentional drifts detected")
    print("Report:", args.report)
    return 0 if s["all_expectations_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
