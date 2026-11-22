"""Versioned synthetic rule constants, normalization and immutable decision contract."""
from __future__ import annotations
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
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



@dataclass(frozen=True)
class Decision:
    clinical: str
    communication: str
    reasons: tuple[str, ...]
    rule: str
    rule_version: str


