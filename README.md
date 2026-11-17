# Kenya FHIR Conformance Fixtures

**A Peton Labs open-source project (local working draft; GitHub repository not created).**

Small, auditable synthetic FHIR R4 resources intended to become executable conformance tests against the **Kenya Core FHIR IG `ke.fhir.core#1.0.0`**.

> **STATUS: CANDIDATE FIXTURES ONLY — NOT HL7 VALIDATOR VERIFIED.** Passing the local integrity checks does not establish FHIR/IG conformance, DHA approval or certification.

## Why this exists

The national Kenya Core IG already publishes extensive positive examples. This project is **not** a second example gallery. It focuses on **reproducible positive/negative test cases with machine-checkable expectations** that implementers can run in CI. Cases exercise a particular constraint and fail when a validator produces an unexpected error (including an unrelated error).

## Current contents

- 12 independently authored synthetic candidate resource fixtures: 6 positive, 6 deliberately invalid; Patient, Encounter and ServiceRequest.
- `manifest.json` maps every fixture to an expected outcome, canonical profile, and for negative cases, a source-traceable path/constraint.
- Pure-Python fixture-integrity checks and `unittest` tests (no dependencies).
- Optional CLI runner for official HL7 Java validator, requiring locally provisioned verified validator JAR and `ke.fhir.core#1.0.0` FHIR package archive.

## Quick start: offline fixture integrity only

```bash
python3 scripts/check_fixtures.py
python3 -m unittest discover -s tests -v
```

**These are NOT FHIR conformance checks.** They verify JSON structure, catalog consistency, controlled mutations and local expectations.

## True conformance validation (not yet executed)

1. Download official `validator_cli.jar` from [HL7 validator releases](https://github.com/hapifhir/org.hl7.fhir.core/releases/latest), verify its release and checksum.
2. Obtain the real FHIR NPM package for `ke.fhir.core#1.0.0`, verify `package/package.json` and record SHA-256. Do **not** substitute a different version or canonical base without updating the manifest and fixtures.
3. Run:

```bash
python3 scripts/run_validator.py --jar /path/to/validator_cli.jar --ig /path/to/ke.fhir.core-1.0.0.tgz
```

The runner uses the expected profile explicitly, parses `OperationOutcome`, and requires negative test cases to fail for the **targeted** reason without unrelated errors. It exits nonzero on missing prerequisites or inconclusive output. See [VALIDATION.md](VALIDATION.md).

## Sources and governance

- [Published IG landing page](https://fhir.dha.go.ke/ig/core/)
- [Patient profile](https://fhir.dha.go.ke/ig/core/StructureDefinition-kenya-core-patient-definitions.html)
- [Encounter profile](https://fhir.dha.go.ke/ig/core/StructureDefinition-kenya-core-encounter.html)
- [ServiceRequest profile](https://fhir.dha.go.ke/ig/core/StructureDefinition-kenya-core-servicerequest.html)
- [Upstream IG examples](https://fhir.dha.go.ke/ig/core/artifacts.html)
- [Upstream QA report](https://fhir.dha.go.ke/ig/core/qa.html)

The IG site currently labels 1.0.0 a release, but its QA report also lists publication-process notices and 195 errors. It is a provenance and upstream-quality risk to investigate, not proof the profiles are unusable.

All patient details, IDs and phone numbers here are intentionally artificial placeholders. Do not submit them to any real SHA/DHA service, use them for eligibility checks, or interpret them as Kenyan population simulations.

**Independent work, not affiliated with, approved, or certified by Kenya's Digital Health Agency.** Do not imply certification. No employer-owned code/data or patient information used.

## Contribution criteria

A new fixture must (1) cite the exact IG path/constraint, (2) contain no real patient data, (3) have a declared expected validation result, (4) demonstrate no unrelated errors, and (5) pass the pinned official validator in CI before being called *verified*.

## Next release gate

Package acquisition + fingerprint, full validator run, fixtures repaired to zero unexpected errors, then GitHub publishing and community verification. See [NEXT-STEPS.md](NEXT-STEPS.md).
