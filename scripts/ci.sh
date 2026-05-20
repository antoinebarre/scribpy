#!/usr/bin/env bash
# Runs all CI checks without early exit, then prints a consolidated summary.
# Exit code = number of failed checks (0 = all passed).

set -uo pipefail

G='\033[32m' R='\033[31m' Y='\033[33m' B='\033[1m' N='\033[0m'
SEP='━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

# CI writes every tool output under work/ so the same files can be uploaded as
# artifacts by the pipeline when a job fails.
mkdir -p work
export UV_CACHE_DIR="${UV_CACHE_DIR:-work/.uv-cache}"

PASS=0
FAIL=0
declare -a FAIL_NAMES=()
TEST_INFO=''

# ── helpers ───────────────────────────────────────────────────────────────────

run() {
    local name=$1 log=$2; shift 2
    printf " %-16s  " "$name"

    # Unlike a normal Make recipe, CI should continue after failures to reveal
    # all broken gates in one run. The final exit code is the number of failures.
    if "$@" >"$log" 2>&1; then
        printf "${G}✔ pass${N}\n"
        PASS=$((PASS + 1))
    else
        printf "${R}✘ FAIL${N}\n"
        FAIL=$((FAIL + 1))
        FAIL_NAMES+=("$name")
    fi
}

contains() {
    local needle=$1; shift
    for item; do [ "$item" = "$needle" ] && return 0; done
    return 1
}

# ── checks ────────────────────────────────────────────────────────────────────

printf "\n${B}Running CI checks…${N}\n\n"

# CI uses format-check instead of format so it never mutates the checked-out
# source tree. The local check script intentionally formats files for developers.
run "format-check"  work/format.log    uv run ruff format --check src/ scripts/
run "lint"          work/lint.log      uv run ruff check  src/ scripts/
run "docstrings"    work/docstrings.log uv run ruff check src/ --select D --ignore D100,D104
run "docstrings-strict" work/docstrings-strict.log uv run python scripts/check_google_docstrings.py
run "init-modules"      work/init-modules.log      uv run python scripts/check_init_modules.py
run "type-check"    work/typecheck.log uv run mypy src/
run "metrics"       work/metrics.log   uv run python scripts/code_metrics.py
run "security-code" work/security-code.log uv run bandit -c pyproject.toml -r src scripts
run "security-deps" work/security-deps.log bash scripts/security_audit_deps.sh

# Tests — exit code 5 means no tests were collected; treat as pass.
printf " %-16s  " "tests"
uv run pytest >work/test.log 2>&1; rc=$?
[ "$rc" -eq 5 ] && rc=0
if [ "$rc" -eq 0 ]; then
    t=$(grep -oE '[0-9]+ passed' work/test.log | tail -1 || true)
    c=$(awk '/^TOTAL/{print $NF}' work/test.log | tail -1 || true)
    TEST_INFO="${t:+$t · }coverage ${c:--}"
    printf "${G}✔ pass${N}  %s\n" "$TEST_INFO"
    PASS=$((PASS + 1))
else
    printf "${R}✘ FAIL${N}\n"
    FAIL=$((FAIL + 1))
    FAIL_NAMES+=("tests")
fi

# ── failure details ───────────────────────────────────────────────────────────

if [ "${#FAIL_NAMES[@]}" -gt 0 ]; then
    for name in "${FAIL_NAMES[@]}"; do
        # Keep this mapping close to the check list above. If a check is added,
        # add its log here so CI failure output stays actionable.
        case $name in
            format-check) log=work/format.log    ;;
            lint)         log=work/lint.log      ;;
            docstrings)   log=work/docstrings.log ;;
            docstrings-strict) log=work/docstrings-strict.log ;;
            init-modules) log=work/init-modules.log ;;
            type-check)   log=work/typecheck.log ;;
            metrics)      log=work/metrics.log   ;;
            security-code) log=work/security-code.log ;;
            security-deps) log=work/security-deps.log ;;
            tests)        log=work/test.log      ;;
            *)            log=''                 ;;
        esac
        printf "\n${Y}%s${N}\n${Y}── %s errors ──${N}\n" "$SEP" "$name"
        [ -n "$log" ] && cat "$log"
    done
fi

# ── summary ───────────────────────────────────────────────────────────────────

TOTAL=$((PASS + FAIL))
printf "\n${B}%s${N}\n" "$SEP"
printf "${B} %-16s  %-10s  %s${N}\n" "Check" "Status" "Details"
printf "${B}%s${N}\n" "$SEP"

for name in "format-check" "lint" "docstrings" "docstrings-strict" "init-modules" "type-check" "metrics" "security-code" "security-deps" "tests"; do
    # This summary is intentionally compact. Detailed diagnostics have already
    # been printed for failed checks and full logs remain in work/.
    case "$name" in
        metrics) details="report work/code-metrics-report.md" ;;
        security-code) details="Bandit SAST" ;;
        security-deps) details="pip-audit runtime dependencies" ;;
        tests)   details="$TEST_INFO" ;;
        *)       details='' ;;
    esac
    if ! contains "$name" "${FAIL_NAMES[@]+"${FAIL_NAMES[@]}"}"; then
        printf " %-16s  ${G}✔ pass${N}      %s\n" "$name" "$details"
    else
        printf " %-16s  ${R}✘ FAIL${N}      %s\n" "$name" "$details"
    fi
done

printf "${B}%s${N}\n" "$SEP"
if [ "$FAIL" -eq 0 ]; then
    printf " ${G}${B}All %d checks passed.${N}\n\n" "$TOTAL"
else
    printf " ${R}${B}%d of %d checks failed.${N}\n\n" "$FAIL" "$TOTAL"
fi

# Generate quality reports (never blocks exit code)
if uv run python scripts/report_files.py >>work/reports.log 2>&1 && \
   uv run python scripts/report_lint.py  >>work/reports.log 2>&1 && \
   uv run python scripts/report_metrics.py >>work/reports.log 2>&1 && \
   uv run python scripts/report_tests.py >>work/reports.log 2>&1 && \
   uv run python scripts/assemble_report.py >>work/reports.log 2>&1; then
    printf " ${G}Quality report: work/quality_report.md${N}\n"
    printf " ${G}Artefacts zip:  work/quality_artefacts.zip${N}\n"
else
    printf " ${Y}Warning: report generation had errors (see work/reports.log)${N}\n"
fi

exit "$FAIL"
