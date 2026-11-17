#!/usr/bin/env bash
# Fetch pinned validator + Kenya Core package, then verify SHA-256. Fails closed on any mismatch.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p deps
JAR_URL=https://github.com/hapifhir/org.hl7.fhir.core/releases/download/7.0.6/validator_cli.jar
# Immutable mirror of the exact tested DHA build (DHA's URL can be rebuilt in place under the same version).
IG_MIRROR=https://github.com/petonlabs/kenya-fhir-fixtures/releases/download/ig-ke.fhir.core-1.0.0-20261002/ke.fhir.core-1.0.0.tgz
IG_ORIGIN=https://fhir.dha.go.ke/ig/core/package.tgz
[ -f deps/validator_cli.jar ] || curl -fsSL -o deps/validator_cli.jar "$JAR_URL"
[ -f deps/ke.fhir.core.tgz ] || curl -fsSL -o deps/ke.fhir.core.tgz "$IG_MIRROR" || curl -fsSL -o deps/ke.fhir.core.tgz "$IG_ORIGIN"
shasum -a 256 -c deps.sha256
