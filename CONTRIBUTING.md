# Contributing

v0.1 scope is frozen at 12 fixtures. Bug reports about the fixtures, the runner or upstream IG findings are welcome.

A fixture change or addition must:

1. Cite the exact profile element, invariant key or binding, plus its source URL, in `manifest.json` (`rule`, `source_profile_url`), and set `constraint_scope` to `kenya-core` or `base-r4`.
2. Contain only synthetic data (ids start with `synthetic-`; placeholder identifiers only).
3. For a negative: be its `negative_of` positive with exactly one `mutation`, and declare the full `expected_errors` signature set.
4. Pass `check_fixtures.py`, the unit tests, and `run_validator.py` locally and in CI.

Never edit a fixture just to hide an upstream IG defect. Document the defect in `VALIDATION.md` and report it to the [IG maintainers](https://github.com/IntelliSOFT-Consulting/Kenya-core-FHIR-IG).

Bumping the validator or the IG build means updating `deps.sha256`, `manifest.json` (`ig`/`validator`) and `scripts/fetch_deps.sh`, then committing a fresh `results/validation.json`.
