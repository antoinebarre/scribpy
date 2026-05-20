#!/usr/bin/env bash
# Audit runtime package dependencies for known vulnerabilities.

set -euo pipefail

mkdir -p work
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
# PYSEC-2026-89 affects Python-Markdown versions before 3.8.1; the lockfile
# currently resolves markdown to 3.10.2, so pip-audit's match is a false positive.
uv run pip-audit \
    --strict \
    --progress-spinner off \
    --requirement work/requirements-audit.txt \
    --no-deps \
    --disable-pip \
    --ignore-vuln PYSEC-2026-89
