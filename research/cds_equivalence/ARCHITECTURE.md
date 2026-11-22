# ADR 001 — Evidence-first cross-HMIS equivalence

**Status:** research foundation only, synthetic. **Date:** 2026-11-22.

## Architectural decision

Remain within the Peton Labs conformance fixture repository, but isolate the
synthetic equivalence research track. Do **not** build a general-purpose CDSS
or claim clinical validation from comparing one fictional training rule.

The system has four major boundaries:

```text
Synthetic FHIR / synthetic legacy records
          |                 |
        adapters.py (source-specific, fail-closed)
                     |
   canonical facts + workflow assertions + source hashes
          |                                |
    engine.py (pure)                comparison.py
          |                                |
  discrete training decision       six-axis equivalence
          +---------------+----------------+
                          |
                   equivalence.py
             scenarios, audit report, exit code
                          |
                independently run CI
```

## Six invariants

1. **Subject and encounter:** patient and encounter links must be consistent.
2. **Clinical evidence:** identical codes, normalized values, finality,
   time instants and scope are checked independently of outcome labels.
3. **Rule identity:** rule ID and version must match.
4. **Clinical outcome:** an independently executable, deterministic policy
   yields a recommendation or explicit abstention.
5. **Authorization:** messaging eligibility is a separate workflow gate,
   not proof of consent, legal basis or permission to actually transmit.
6. **Audit:** every comparison records axes, reason codes, source fingerprints
   and policy version. SHA-256 here is traceability, NOT tamper protection.

The strict equivalence relation is the conjunction of six checks:
normalized evidence, clinical decision, communication authorization,
reason codes, workflow context, and rule identity.

Matching outcome labels with materially different patient evidence is NOT
equivalence. Likewise, matching clinical decisions despite divergent
communication consent is NOT workflow equivalence.

## Trust boundaries and failure modes

- **Source -> adapter:** external source fields are untrusted.
  Duplicate resources, ambiguous codes and unknown UCUM systems lead to
  adapter issues and mandatory abstention; do not pick the first/last
  clinical record without explicit resolution.
- **Adapter -> engine:** no networking, language models, implicit defaults,
  source-specific branching or writes in the clinical rule.
- **Engine -> consumer:** fictional toy haemoglobin thresholds are not
  approved or current clinical guidance; the engine never sends messages.
- **Consumer -> transport:** no transport is implemented. Eligibility
  for human approval is NOT authorization to share patient information.
- **Test -> claims:** local Bundle shape checks are NOT an HL7 validator;
  original profile CI only validates the original 12 fixtures.

## Explicit out-of-scope items

Real patient records; SHA/DHA private APIs; vendors' licensed code;
CHAIRII/Chunguza derivative code; approved WHO/DAK algorithms;
actual FHIR Consent; external terminology verification; independently
adjudicated clinical correctness; protected/cryptographically signed
audit logs; production threat model; independent HMIS implementations.

## Gate for next phase

1. Independent clinical owner selects dated national guideline and policy.
2. Blinded clinician/methodologist creates reference decisions independently.
3. Each claimed conformant input is validated using pinned external FHIR
   tooling and appropriate terminology verification.
4. Two genuinely independent HMIS adapters are supplied and reviewed.
5. Analyze four outcomes: both correct, A only correct, B only correct,
   both wrong, while measuring safe abstention separately.
6. Before any patient-data access, obtain institutional, ethics,
   privacy, device-classification and deployment approvals as applicable.

**Stop condition:** if upstream data lacks necessary provenance or clinical
ownership is unavailable, focus on data-quality and validation infrastructure,
not adding rules to a CDS engine.

## Why deliberately no plugin architecture yet?

A single fictional pathway does not establish a reusable clinical rule API.
Premature generalization would hard-code incorrect abstractions. Derive the
next interface only after an independently adjudicated second pathway.
