"""Adapters for two synthetic HMIS representations, not certified FHIR validation."""
from __future__ import annotations
from typing import Any
from contracts import SYSTEM_LOINC, HB_LOINC, MAPPING_VERSION, digest, fhir_ref, normalize_hb

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


