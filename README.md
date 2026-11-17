# Kenya FHIR Conformance Fixtures

[![CI](https://github.com/petonlabs/kenya-fhir-fixtures/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/petonlabs/kenya-fhir-fixtures/actions/workflows/ci.yml)

An independent, open-source Peton Labs project. These are 12 small synthetic FHIR R4 resources, each with a machine-checkable expected outcome against the DHA **Kenya Core IG `ke.fhir.core#1.0.0`**. Each case is checked with the official HL7 validator in CI.

> **Status:** all 12 cases matched their expected outcome with HL7 validator 7.0.6, the pinned Kenya Core package, and `-tx n/a` ([report](results/validation.json)). This is **not** DHA approval or certification, and it does not cover terminology validation (see [VALIDATION.md](VALIDATION.md)).

## What this is (and isn't)

The Kenya Core IG already publishes positive examples. This repo adds **negative** cases. Each one is a positive fixture with a single field mutated, and it must fail with **exactly** the declared set of error-level issues: no fewer, no extra. Use these cases to check that your validator or pipeline actually enforces the Kenya Core rules.

It is not an example gallery, a Synthea generator, an SHA/DHA integration, or a certification service.

## Test matrix

| Fixture | Expect | Error signature(s) required | Scope |
| --- | --- | --- | --- |
| `patient-national-id` | pass | none | |
| `patient-phone` | pass | none | |
| `patient-no-identifier` | fail | `min:Patient.identifier`, `invariant:sha-patient-min-identifier` | Kenya Core |
| `patient-future-birth-date` | fail | `invariant:valid-birth-date` | Kenya Core |
| `encounter-ambulatory` | pass | none | |
| `encounter-in-progress` | pass | none | |
| `encounter-no-subject` | fail | `min:Encounter.subject` | Kenya Core (base R4 is 0..1) |
| `encounter-no-class` | fail | `min:Encounter.class` | base R4 |
| `servicerequest-lab` | pass | none | |
| `servicerequest-referral` | pass | none | |
| `servicerequest-no-subject` | fail | `min:ServiceRequest.subject` | base R4 |
| `servicerequest-no-authored-on` | fail | `min:ServiceRequest.authoredOn` | Kenya Core (base R4 is 0..1) |

Warnings and information issues are recorded in the report but don't decide pass/fail. Every resource carries the `dom-6` (no narrative) warning, and Encounter adds a draft-CodeSystem info note.

## Reproduce (macOS / Linux)

Needs Java 17+, Python 3.10+, `curl` and `shasum`. No pip dependencies.

```bash
python3 scripts/check_fixtures.py            # fixture/manifest integrity (NOT conformance)
python3 -m unittest discover -s tests -v     # integrity + runner logic
scripts/fetch_deps.sh                        # pinned validator + IG, SHA-256 verified
python3 scripts/run_validator.py             # real validation → results/validation.json
```

The first validator run downloads the registry dependencies (`hl7.fhir.r4.core`, `hl7.terminology.r4`, …) into `~/.fhir/packages`.

## Provenance

| Artifact | Version | Source | SHA-256 |
| --- | --- | --- | --- |
| HL7 validator | 7.0.6 | [GitHub release](https://github.com/hapifhir/org.hl7.fhir.core/releases/tag/7.0.6) | `2686590539f0b3ba7683149b25d78249f6886c04e2c326e884c5049d8947df89` |
| Kenya Core | `ke.fhir.core#1.0.0`, build `20261002090010`, canonical `https://fhir.dha.go.ke/core`, FHIR 4.0.1 | [DHA origin](https://fhir.dha.go.ke/ig/core/package.tgz) · [immutable mirror](https://github.com/petonlabs/kenya-fhir-fixtures/releases/tag/ig-ke.fhir.core-1.0.0-20261002) | `59a7d93f5b7691e31d27d8af62ba029fff40083e4b5c1e518ae7c76d630dedd9` |

Kenya Core is not on packages.fhir.org. DHA can rebuild `package.tgz` in place under the same version, so CI downloads our mirror of the exact tested build (licensed CC0-1.0). The mirror is hash-checked, and the DHA URL is the fallback. See [SOURCES.md](SOURCES.md) for caveats: the package declares `notForPublication: true`, and the QA report lists errors.

## Synthetic data and affiliation

All identifiers, names and phone numbers are artificial placeholders. Never submit them to SHA/DHA services. Peton Labs is **not affiliated with, approved or certified by** Kenya's Digital Health Agency. Code is under the MIT licence ([LICENSE](LICENSE)). Kenya Core content is DHA's, under CC0-1.0.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Scope is frozen at these 12 fixtures for v0.1.
