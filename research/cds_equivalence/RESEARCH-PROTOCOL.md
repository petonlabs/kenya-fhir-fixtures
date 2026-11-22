# Protocol 001 — Cross-HMIS clinical equivalence as a measurable safety property

**Institutional home:** Peton Labs (independent research engineering). **Phase:** preclinical, synthetic methods development. **Date:** 2026-11-22. **Interventions/patient access:** none. **Guideline clinical validation:** none. **Conflict-of-interest boundary:** no SHA private interfaces, Ginja employer artifacts, HMIS vendor onboarding, or real patient data. Do not incorporate CHUNGUZA workshop source under its CC BY-NC-ND licence.

## 1. Parent problem and competing explanations

FHIR syntactic and profile conformance is necessary for reliable exchange but does not itself establish that a resource is about the intended patient, that observations are timely/final, that local codes preserve meaning, or that subsequent actions are authorized. A system could pass structural checks yet drive unsafe downstream behavior. Conversely, an apparent discrepancy between systems might reflect a legitimate difference in clinical context or local policy rather than an adapter bug.

The first *engineering* question is whether a contract-based test kit can distinguish equivalent representations from deliberately corrupted ones. The later *clinical* question is whether independent implementations agree with externally adjudicated guideline decisions in representative cases.

## 2. Research questions and falsifiable hypotheses

- **RQ1:** Given clinically equivalent synthetic evidence, do two separately implemented source adapters produce identical normalized decision inputs and clinical outcomes?
- **RQ2:** Can we detect specified discrepancies in identity, encounter linkage, status, time, units, coding and authorization that are not adequately captured by a resource-level schema check?
- **RQ3 (future):** Under independently adjudicated guideline reference cases, how often do vendor implementations produce clinically wrong, missing or unsafe recommendations?

**H1:** For all explicitly equivalent cases in the predefined fixture set, the deterministic evaluation produces the same decision and communication-authorization results.
**H2:** For all predefined corruption cases, a report produces a discrepancy or abstention with an actionable reason code.

These are **finite test-suite hypotheses**, not population estimates. Results must not be generalized beyond supplied scenarios without further evidence.

## 3. Formal model

Let `A_s` be a source-specific adapter and `R_v` a versioned deterministic rule. Let `X_s` be the source record and `W_s` the verified workflow context. Define `C_s = A_s(X_s, W_s)`, then `D_s = R_v(C_s)`.

For an explicitly defined equivalence relation `≈_v` over the facts required by the rule:

`C_A ≈_v C_B  =>  decision(R_v(C_A)) == decision(R_v(C_B))`

This holds only if both adapters preserve clinically relevant facts and the rule is evaluated in the same policy context. Passing equivalence does **not** imply correctness: two systems can agree on the same wrong answer. Therefore add an independent reference oracle in the next phase and compare `D_A` and `D_B` to it, not merely to each other.

A useful future **four-way classification** is `both correct / A only correct / B only correct / both incorrect`; also classify `unsafe action`, `correct abstention`, and `clinical context mismatch` separately.

## 4. Layers of evidence and non-substitutability

| Layer | Proposed method | Status here |
|---|---|---|
| JSON shape | Decoding and structure checks | Narrow local check only |
| FHIR conformance | Official HL7 validator with pinned Kenya Core IG | Existing repo baseline; **not run on these new cases** |
| Terminology | Declared coding systems, explicit ConceptMaps and independent review | Tiny local demonstration only |
| Semantic mapping | Provenance-rich canonical contract and metamorphic input variations | Implemented for two synthetic adapters |
| Clinical decision equivalence | Versioned deterministic policy applied to both adapters | Implemented for one fictional rule |
| Workflow safety | Explicit person, encounter, status, timestamp and consent invariants | Implemented for enumerated cases |
| Independent clinical validity | Clinical adjudication against dated guideline + cases designed by other researchers | **Not yet done** |
| Production performance | Shadow mode, workflow usability, alert fatigue, outcomes and incident surveillance | **Not yet done** |

## 5. Experiment, independent variables and endpoints

- **Sources:** A small synthetic FHIR R4-shaped Bundle vs a fictional legacy EMR relational record.
- **Constant:** policy ID/version, evaluation date, clinical eligibility, outcome categories.
- **Manipulated:** source-specific representation and one corrupt/ambiguous fact at a time.
- **Primary endpoint:** predefined equivalence / non-equivalence classification matches observed results.
- **Secondary:** safety invariants identify reasons; result reproducibility; no communications sent; audit report contains hashes and source links.
- **Negative controls:** equivalent nonfinal cases must yield matched safe abstentions, not recommendations.
- **Error taxonomy:** `identity`, `encounter`, `status`, `time`, `unit`, `code`, `consent`, `scope`, `undetermined`.
- **Reporting:** produce both counts and per-case traces; never report `certified` or `clinically validated`.

## 6. Independent clinical-phase design

For the next phase, **before modifying the engine**, select one authoritative published and dated guideline relevant to Kenyan practice, with explicit national adaptations and decision tables. Obtain an independent clinician/methodologist who writes a hidden reference set. Pre-register the inclusion/exclusion criteria, eligible population, temporal validity, adjudication method, harm-weighted discrepancies, rule version, mapping assumptions, and intended clinical workflow. Report both agreement and uncertainty; inspect failure clustering and false-safe recommendations. Do not silently drop abstentions from accuracy denominators.

Use three distinct roles where feasible: clinical rule owner; adapter implementer; independent clinical evaluator. Avoid deriving the oracle from the same executable code. Assess privacy, ethics and intended-use classification before any real-data shadow mode.

## 7. Decision gates

1. **Technical methods gate:** all synthetic controls pass, injected drifts are detected, and CI reproducibly reports a pinned toolchain.
2. **FHIR conformance gate:** each newly claimed 'FHIR-valid' resource is actually validated against the relevant versioned profile using the official validator; otherwise label as FHIR-shaped only.
3. **Clinical authority gate:** rule, interpretation and independent reference set have clinical owner and sign-off.
4. **Cross-HMIS gate:** at least two genuinely independent implementations (not just two inputs to the same runtime), with an explicitly reconciled equivalence relation.
5. **Prospective feasibility gate:** only after regulatory and institutional permissions, evaluate in non-interventional shadow mode before considering active CDS.

**Stop condition:** if failures concentrate in unresolvable source-data omissions or institutional ownership is unavailable, do not expand the rule library. Focus on data quality, provenance or conformance tooling instead.

## 8. Source register (reference, not a validation claim)

- DHA Kenya Core IG v1.0.0: https://fhir.dha.go.ke/ig/index.html
- DHA Kenya Core Artifacts, including Provenance: https://fhir.dha.go.ke/ig/artifacts.html
- HL7 FHIR R4 GuidanceResponse: https://hl7.org/fhir/R4/guidanceresponse.html
- CDS Hooks 2.0.1: https://cds-hooks.hl7.org/
- Peton Labs existing v0.1 conformance baseline: https://github.com/petonlabs/kenya-fhir-fixtures

This prototype defines its own deliberately fictional training thresholds. It does not represent WHO SMART Guidance, Kenya national clinical guidance, or an adapted DAK.
