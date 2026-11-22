#!/usr/bin/env python3
"""Synthetic cross-HMIS decision equivalence experiment runner."""
from __future__ import annotations
import argparse
import copy
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any
from contracts import POLICY, RULE_ID, RULE_VERSION, REFERENCE_TIME, MAPPING_VERSION, SCHEMA_VERSION
from contracts import SYSTEM_LOINC, HB_LOINC, Decision, digest
from adapters import canonical
from engine import decide

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
