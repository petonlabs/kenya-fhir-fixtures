# Work queue / decision gates

1. **P0 — Verify package provenance**: Obtain `ke.fhir.core#1.0.0` from a trustworthy package registry or IG build archive, hash it, and verify canonical/declared dependencies. Identify whether 1.0.0 is actually registry-published; QA says "This IG has never been published" even though the site labels the build a release.
2. **P0 — Execute HL7 validator**: Run 12 fixtures; check negative failure messages, patch unexpected issues; store verified manifest and reproducible output. Do not publish a conformance badge until this passes.
3. **P1 — Minimal CI**: Add verified JAR/package checksum or immutable release source. Fail closed if dependencies are unavailable. Current CI only checks fixture integrity.
4. **P1 — Upstream feedback**: Open a carefully evidenced issue / share with IG maintainers, emphasizing complementarity to existing examples and reporting any IG defects independently.
5. **P2 — Useful journeys**: Once atomic cases are sound, add one patient + encounter + request bundle with local reference integrity, and then intentional cross-resource failures (distinct from structure validation).
6. **Stop condition**: If conformant examples and robust validator suites already cover these failure classes upstream, contribute enhancements there instead of maintaining duplicate infrastructure.

**Repository destination under discussion**: `peton-labs/kenya-fhir-fixtures` (not created/published as part of this local bundle).
