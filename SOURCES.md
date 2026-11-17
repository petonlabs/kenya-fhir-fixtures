# Source ledger · checked 2026-11-17

| Ref | Source | Finding |
| --- | --- | --- |
| IG-001 | https://fhir.dha.go.ke/ig/core/ | DHA site labels `ke.fhir.core#1.0.0` (FHIR R4) a release, generated 2026-10-02 |
| IG-PKG | https://fhir.dha.go.ke/ig/core/package.tgz | Inspected locally. `package.json`: name `ke.fhir.core`, version `1.0.0`, date `20261002090010`, canonical `https://fhir.dha.go.ke/core`, fhirVersions `4.0.1`, license CC0-1.0, **`notForPublication: true`**, `url: file:///ig/output`. SHA-256 `59a7d93f…dedd9` |
| IG-DEPS | same | Depends on `hl7.fhir.r4.core#4.0.1`, `hl7.terminology.r4#7.4.0`, `hl7.fhir.uv.extensions.r4#5.3.0`, `hl7.fhir.uv.ips#1.1.0` (all from packages.fhir.org) |
| IG-REG | https://packages.fhir.org/ke.fhir.core | Not present in the official registry |
| IG-002 | https://fhir.dha.go.ke/ig/core/artifacts.html | Positive examples already exist upstream, so this repo focuses on negatives |
| IG-003 | `StructureDefinition-kenya-core-patient.json` (in package) | `sha-patient-min-identifier` (error), `valid-birth-date` (error), `national-id-format` / `kenya-phone-format` / `household-number-format` (**warning**), `identifier` min=1 |
| IG-004 | `StructureDefinition-kenya-core-encounter.json` | `subject` min=1; `class` unchanged from base (1..1) |
| IG-005 | `StructureDefinition-kenya-core-servicerequest.json` | `authoredOn` min=1; `subject` unchanged from base (1..1) |
| IG-007 | https://fhir.dha.go.ke/ig/core/qa.html | QA report lists errors/warnings and says the IG has never been published through the official process |
| IG-008 | https://github.com/IntelliSOFT-Consulting/Kenya-core-FHIR-IG | Upstream source. No negative fixtures or validator test suite found in the repo tree (2026-11-17) |
| IG-009 | https://fhir.dha.go.ke/ig/core/ServiceRequest-example-servicerequest-amina-fhg.json.html | LOINC `58410-2` used upstream, so it is reused here as a code only |
| VAL | https://github.com/hapifhir/org.hl7.fhir.core/releases/tag/7.0.6 | `validator_cli.jar` SHA-256 `26865905…df89` |

**Canonical collision:** older or alternate builds use `kenya.fhir.core` and a `fhir.sha.go.ke` canonical. This repo uses **only** the DHA `ke.fhir.core` / `https://fhir.dha.go.ke/core` package, and the runner refuses any other.

**What "release" means here:** DHA's site calls 1.0.0 a release, but the package itself is flagged `notForPublication` and the QA report raises publication concerns. Treat it as the current DHA build, not a formally published, immutable FHIR package.
