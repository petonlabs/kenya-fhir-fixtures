# Validation contract

**Local tests prove fixture construction only.** The two distinct questions are:

1. *Integrity*: Is each example valid JSON with intended positive or targeted-negative mutation? `check_fixtures.py` answers this.
2. *FHIR conformance*: Does a specific version of the HL7 Validator with the exact `ke.fhir.core#1.0.0` package validate positive fixtures, and reject negatives **for only their intended reason**? Only `run_validator.py` with the actual pinned artifacts can answer this.

### Strictness

- A positive case with ANY error-level `OperationOutcome.issue` fails (warnings recorded, not automatically failures).
- A negative case must have at least one error and the **intended path and/or invariant** must be visible in the error-level output. All other error-level issues are treated as unexpected. Current matching is conservative and may require tuning to the exact official validator wording.
- Infrastructure failures, missing packages, unsupported `-output` format and dependency errors are **BLOCKED**, not passed.
- An IG version upgrade requires its own revalidation and explicit fixture change review.

### Prerequisites

Java 17+, standard library Python 3.10+, the official validator JAR and a *locally supplied* FHIR NPM tarball containing `package/package.json` with name `ke.fhir.core`, version `1.0.0`, FHIR R4. For repeatability, record SHA-256 of both binaries; this template does not imply they are locked yet.

### Known upstream issue

[Kenya Core QA report 2026-10-02](https://fhir.dha.go.ke/ig/core/qa.html) reports errors and publication-process warnings. Treat widespread terminology/profile errors as a separate upstream workstream; never rewrite fixtures solely to hide a defect in the authoritative IG.

**Terminology limit:** `-tx n/a` avoids a network terminology server; local binding checks depend on what the pinned package and dependencies contain. It must not be represented as exhaustive clinical terminology validation.
