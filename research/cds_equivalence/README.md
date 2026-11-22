# Peton Labs — Cross-HMIS Clinical Decision Equivalence (technical proof)

**Status:** Independently implemented synthetic experiment. **NOT clinical software, a clinical guideline implementation, a Kenya Core conformance result, DHA endorsement, or Chunguza derivative.** All patient identifiers and contact numbers are fabricated. Do not use these thresholds for care.

## Research question

Can two different HMIS representations yield identical, auditable decisions when they represent equivalent clinical facts? Can specified safety-relevant transformations be detected even when ordinary structural validation would not establish the clinical relationship?

Two independently authored synthetic adapters ingest (A) an FHIR R4-shaped Patient/Encounter/Observation Bundle and (B) a relational/legacy-HMIS record. Both yield a common clinical context; a deterministic training-only rule returns a clinical review tier, a distinct communication authorization outcome, and reason codes.

The policy's toy haemoglobin thresholds (7 and 10 g/dL) exist solely to make the software experiment executable. They are **not sourced from, reviewed against, or presented as clinical guidance**. Clinical scope deliberately requires adult, nonpregnant context; it abstains for anything else. No action is sent or performed.

## Reproduce

```bash
python3 equivalence.py --report reports/equivalence.json
python3 -m unittest discover -s tests -v
```

No external packages, network, patient data, APIs, LLMs, secrets, or system clock required. Supports Python >=3.10. The reference time is pinned to 2026-11-22T12:00:00+03:00.

## Test matrix

| ID | Synthetic transformation | Expectation |
| --- | --- | --- |
| 01 | Final haemoglobin 6.8 g/dL across both representations | Equivalent |
| 02 | Both inputs 12.1 g/dL | Equivalent |
| 03 | Legacy 68 g/L converted to 6.8 g/dL | Equivalent |
| 04 | Both inputs preliminary | Equivalent safe abstention |
| 05 | Legacy result attached to a different patient | Detect divergence |
| 06 | Legacy result too old | Detect divergence |
| 07 | Legacy result still draft | Detect divergence |
| 08 | Legacy unit unmapped | Detect divergence |
| 09 | Legacy result timestamp in future | Detect divergence |
| 10 | Legacy local code unmapped | Detect divergence |
| 11 | Legacy message consent absent | Detect communication divergence despite same clinical recommendation |
| 12 | Legacy identity not explicitly verified | Detect divergence |

## Precise properties and limitations

* **What equivalence means here:** exact equality of the deterministic outcomes (`clinical`, `communication`, and sorted reason codes). Other applications may require semantic, not exact, equivalence.
* **What an adapter proves:** an explicit transformation from a known synthetic source shape into canonical facts. It does not establish a real vendor's implementation fidelity.
* **What the report proves:** the detector found the 8 deliberately injected differences and correctly accepted 4 equivalence controls, with reproducible source/policy hashes. SHA-256 provides traceability but **not cryptographic attestation or tamper-proof audit**.
* **What the report does not prove:** independently correct clinical recommendations, certified FHIR R4/Kenya Core conformance, safe real-world use, generalization to untested scenarios, or correctness of any external HMIS.
* **FHIR-specific limitation:** `local_fhir_shape_check` only checks Bundle/entry/resource-count structure; it is *not* an HL7 validator. Run official pinned Kenya Core validation using the parent project's existing validator workflow for individual profile fixtures. Extend validator fixture coverage separately; do not label new cases `FHIR-valid` without validation.
* **Terminology-specific limitation:** this experiment checks a small explicit local mapping (`HB` and `HGB` to LOINC `718-7`); it does not call a terminology service or claim terminology assurance.
* **Consent:** the synthetic boolean models a workflow invariant, not a FHIR Consent resource or a complete legal basis for processing. `ELIGIBLE_FOR_HUMAN_APPROVAL` is not delivery authorization.
* **Independence:** control expectations are synthetic fixtures authored alongside the detector, not blinded clinical adjudications.

## Integration with `petonlabs/kenya-fhir-fixtures`

Keep the 12 existing v0.1 profile positive/negative fixtures intact. Add this harness under `research/cds_equivalence/` as a logically separate experimental track, initially as a **draft PR**. Require the existing `scripts/check_fixtures.py`, unit tests and pinned HL7 validation to remain green. Keep this synthetic research track separate from SHA endpoints, vendor onboarding and patient data.

## Next research gate

Have a clinician and independent methods reviewer select an authoritative, dated guideline with an available DAK or decision table. Derive versioned reference tests separately from the adapter/runtime developers. Then introduce independent HMIS implementations and measure semantic agreement, safe abstention, operational feasibility, and adjudicated safety discrepancies.


## Architecture v0.2

The original single-file prototype now has separate modules:
`contracts.py` (normalization, decision schema and version),
`adapters.py` (two independent-shaped synthetic sources),
`engine.py` (deterministic training rule),
`comparison.py` (six strict evidence/decision/workflow equivalence axes),
and `equivalence.py` (CLI, scenarios and reports).

**Important fix:** two different haemoglobin measurements can lead to the
same review tier, yet still fail **evidence equivalence**. A similar
distinction applies to clinical decisions versus simulated messaging consent.

See [ARCHITECTURE.md](ARCHITECTURE.md). This is an assurance experiment,
not a production CDS runtime or a substitute for independent clinical review.
