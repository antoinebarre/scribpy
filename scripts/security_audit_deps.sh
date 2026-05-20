#!/usr/bin/env bash
# Audit runtime package dependencies for known vulnerabilities.

set -euo pipefail

mkdir -p work

# pip-audit can resolve requirements itself, but doing so creates a temporary
# virtualenv and can be fragile across platforms. uv already owns resolution for
# this project, so export the locked runtime dependency set first.
uv export \
    --quiet \
    --frozen \
    --no-dev \
    --no-emit-project \
    --no-annotate \
    --no-header \
    --no-hashes \
    --format requirements-txt \
    --output-file work/requirements-audit.txt

# Vulnerability exceptions are project policy, not runner policy. The helper
# reads [tool.scribpy.security_audit] from pyproject.toml and prints one ID per
# line, which this shell script turns into repeated --ignore-vuln arguments.
ignore_args=()
while IFS= read -r vuln_id; do
    ignore_args+=(--ignore-vuln "$vuln_id")
done < <(uv run python scripts/security_audit_ignored_vulns.py)

# --no-deps and --disable-pip tell pip-audit to audit exactly the pinned export
# above instead of trying to resolve dependencies a second time.
uv run pip-audit \
    --strict \
    --progress-spinner off \
    --requirement work/requirements-audit.txt \
    --no-deps \
    --disable-pip \
    "${ignore_args[@]}"
