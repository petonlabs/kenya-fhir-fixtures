# Source ledger · investigated 2026-11-17

| Ref | Primary source | Finding / role |
| --- | --- | --- |
| IG-001 | https://fhir.dha.go.ke/ig/core/ | Labels `ke.fhir.core#1.0.0` and FHIR R4, generated 2026-10-02 |
| IG-002 | https://fhir.dha.go.ke/ig/core/artifacts.html | Multiple connected positive examples already exist; avoid duplicating an example gallery |
| IG-003 | https://fhir.dha.go.ke/ig/core/StructureDefinition-kenya-core-patient-definitions.html | `sha-patient-min-identifier`, `national-id-format`, phone and household-number invariants |
| IG-004 | https://fhir.dha.go.ke/ig/core/StructureDefinition-kenya-core-encounter.html | Encounter cardinalities and profile URL |
| IG-005 | https://fhir.dha.go.ke/ig/core/StructureDefinition-kenya-core-servicerequest.html | ServiceRequest cardinalities and profile URL |
| IG-006 | https://fhir.dha.go.ke/ig/core/ValueSet-encounter-status-vs.html | Kenya Core Encounter.status value set contains `finished` and `in-progress` |
| IG-007 | https://fhir.dha.go.ke/ig/core/qa.html | QA reports 195 errors, 194 warnings and notes IG has never been officially published; distinguish website labels from confirmed package governance |
| IG-008 | https://github.com/IntelliSOFT-Consulting/Kenya-core-FHIR-IG | Upstream source repository |

| IG-009 | https://fhir.dha.go.ke/ig/core/ServiceRequest-example-servicerequest-amina-fhg.json.html | Verified preferred LOINC lab test code `58410-2` present upstream; used as a terminology reference, not copied as a whole fixture |

**Unresolved:** verify package artifact URL, archive checksum, and the validator version; compare canonical URLs and package dependencies before asserting these fixtures are conformant. This ledger records observed webpages, not a local package inspection.
