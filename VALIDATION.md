# Validation contract

There are two separate questions:

1. **Integrity:** is each fixture valid JSON, catalogued in `manifest.json`, and is each negative exactly its positive plus one declared mutation? `scripts/check_fixtures.py` answers this. It says **nothing** about FHIR conformance.
2. **Conformance:** does HL7 validator 7.0.6 with the pinned `ke.fhir.core#1.0.0` package accept every positive and reject every negative for exactly its intended reason? Only `scripts/run_validator.py` answers this.

## How the runner decides

- Before running, it checks the JAR and IG against `deps.sha256` and checks the package's `name`/`version`/`canonical` against the manifest. Any mismatch stops the run (exit 2).
- It invokes the validator once per profile with `-version 4.0.1 -ig <tgz> -profile <url> -tx n/a`.
- It reduces each `error`/`fatal` issue to a signature:
  - `min:<path>`: message-id `Validation_VAL_Profile_Minimum`
  - `invariant:<key>`: message-id `<profile>#<key>`
  - `other:<message-id>@<expression>`: anything else
- A case **passes only if its set of error signatures equals the manifest's `expected_errors`**. Positives expect `[]`. An extra error fails the case, a missing one fails it, and so does an error on the right path for the wrong reason.
- A missing OperationOutcome, a non-OperationOutcome output, a timeout or a missing fixture entry gives **BLOCKED**, and the run never reports success.
- `results/validation.json` holds the full OperationOutcome for each case. `status: VERIFIED` is written only when all 12 cases pass.

## Limits

- **Terminology:** `-tx n/a` means no terminology server is used, so bindings to external code systems (LOINC, SNOMED CT, v3-ActCode) are **not** checked against those code systems. This is structural and profile validation, not terminology assurance.
- **Network quirk:** the validator refuses NAT64 (`64:ff9b::/96`) addresses as "non-public". The runner passes `-Djava.net.preferIPv4Stack=true`.
- **Re-validation:** an IG rebuild or a validator upgrade requires updating `deps.sha256` and reviewing the results again.

## Upstream findings (not masked)

- `national-id-format` (8-digit national ID), `kenya-phone-format` and `household-number-format` have **warning** severity in Kenya Core 1.0.0. A malformed national ID therefore does not make a resource invalid. The starter's `patient-national-id-7-digits` negative could never fail, so it was replaced by `patient-future-birth-date` (`valid-birth-date`, which is error severity). Whether those format rules should be errors is a question for upstream.
- The [QA report](https://fhir.dha.go.ke/ig/core/qa.html) for this build lists errors and publication-process notices. None of them affected these fixtures.
