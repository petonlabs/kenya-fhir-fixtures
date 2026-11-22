"""Strict synthetic source adapters: refuse ambiguity, never silently select records.

This is *not* Kenya Core conformance validation and makes no claim about
real HMIS data quality or terminology-system verification.
"""
from __future__ import annotations
from typing import Any
from contracts import SYSTEM_LOINC, HB_LOINC, MAPPING_VERSION, digest, fhir_ref, normalize_hb


def _dict(obj: Any) -> dict[str, Any]:
    return obj if isinstance(obj, dict) else {}


def _ref(value: Any, kind: str) -> str | None:
    return fhir_ref(_dict(value).get("reference"), kind)


def canonical(source: str, record: dict[str, Any]) -> dict[str, Any]:
    """Normalize source evidence with adapter issues that force abstention."""
    if not isinstance(record, dict):
        raise ValueError("Expected an object, not a null or list")
    workflow = _dict(record.get("workflow"))
    issues: list[str] = []
    if source == "fhir":
        bundle = _dict(record.get("bundle"))
        entries = bundle.get("entry")
        if bundle.get("resourceType") != "Bundle" or bundle.get("type") != "collection" or not isinstance(entries, list):
            issues.append("FHIR_BUNDLE_SHAPE_INVALID")
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in entries if isinstance(entries, list) else []:
            resource = _dict(_dict(row).get("resource"))
            kind = resource.get("resourceType")
            if not isinstance(kind, str):
                issues.append("FHIR_RESOURCE_TYPE_MISSING")
            else:
                grouped.setdefault(kind, []).append(resource)
        selected = {}
        for kind in ("Patient", "Encounter", "Observation"):
            found = grouped.get(kind, [])
            if len(found) != 1:
                issues.append("FHIR_RESOURCE_CARDINALITY_" + kind.upper())
            selected[kind] = found[0] if len(found) == 1 else {}
        p, encounter, observation = (selected[k] for k in ("Patient", "Encounter", "Observation"))
        codings = _dict(observation.get("code")).get("coding")
        if not isinstance(codings, list) or len(codings) != 1 or not isinstance(codings[0], dict):
            issues.append("FHIR_CODING_AMBIGUOUS_OR_MISSING")
            coding = {}
        else:
            coding = codings[0]
        quantity = _dict(observation.get("valueQuantity"))
        if quantity.get("system") != "http://unitsofmeasure.org":
            issues.append("FHIR_UCUM_SYSTEM_UNVERIFIED")
        if quantity.get("code") not in ("g/dL", "g/L"):
            issues.append("FHIR_UCUM_CODE_UNSUPPORTED")
        raw = {
            "patient": p.get("id"),
            "encounter_patient": _ref(encounter.get("subject"), "Patient"),
            "observation_patient": _ref(observation.get("subject"), "Patient"),
            "status": observation.get("status"),
            "code_system": coding.get("system"), "code": coding.get("code"),
            "value": quantity.get("value"), "unit": quantity.get("code"),
            "when": observation.get("effectiveDateTime"),
            "observation_id": "Observation/" + str(observation.get("id", "unknown")),
            "encounter": encounter.get("id"),
            "observation_encounter": _ref(observation.get("encounter"), "Encounter"),
            "age": workflow.get("age_years"), "pregnant": workflow.get("pregnant"),
        }
    elif source == "legacy":
        person, visit, lab = (_dict(record.get(k)) for k in ("patient", "visit", "lab"))
        statuses = {"released": "final", "draft": "preliminary", "corrected": "amended"}
        codes = {"HB": (SYSTEM_LOINC, HB_LOINC), "HGB": (SYSTEM_LOINC, HB_LOINC)}
        coding_system, code = codes.get(lab.get("test"), (None, None))
        raw = {
            "patient": person.get("key"),
            "encounter_patient": visit.get("patient_key"),
            "observation_patient": lab.get("patient_key"),
            "status": statuses.get(lab.get("state")),
            "code_system": coding_system, "code": code,
            "value": lab.get("number"), "unit": lab.get("uom"),
            "when": lab.get("collected_at"),
            "observation_id": "legacy-lab/" + str(lab.get("key", "unknown")),
            "encounter": visit.get("key"),
            "observation_encounter": lab.get("visit_key"),
            "age": workflow.get("age_years"), "pregnant": workflow.get("pregnant"),
        }
    else:
        raise ValueError("Unknown source adapter. Cannot infer input mapping.")
    return {
        "facts": {**raw, "hb_g_dl": normalize_hb(raw["value"], raw["unit"])},
        "workflow": {
            "identity_verified": workflow.get("identity_verified") is True,
            "consent_to_message": workflow.get("consent_to_message") is True,
            "recipient": workflow.get("recipient"),
            "approved_recipient": workflow.get("approved_recipient"),
        },
        "adapter_issues": sorted(set(issues)),
        "provenance": {
            "adapter": source,
            "mapping_version": MAPPING_VERSION,
            "source_hash_sha256": digest(record),
            "source_ref": raw["observation_id"],
        },
    }
