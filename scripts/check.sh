#!/usr/bin/env bash
# Runs local quality checks with readable progress and a final summary table.
# Unlike CI, formatting is mutating so local developers get automatic fixes.

set -uo pipefail

G='\033[32m' R='\033[31m' Y='\033[33m' B='\033[1m' N='\033[0m'
SEP='━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

mkdir -p work
export UV_CACHE_DIR="${UV_CACHE_DIR:-work/.uv-cache}"

PASS=0
FAIL=0
declare -a FAIL_NAMES=()
DETAIL_FORMAT=''
DETAIL_LINT=''
DETAIL_DOCSTRINGS=''
DETAIL_DOCSTRINGS_STRICT=''
DETAIL_TYPE_CHECK=''
DETAIL_METRICS=''
DETAIL_TESTS=''

run() {
    local name=$1 log=$2; shift 2
    printf " %-20s  " "$name"
    if "$@" >"$log" 2>&1; then
        printf "${G}✔ pass${N}"
        PASS=$((PASS + 1))
    else
        printf "${R}✘ FAIL${N}"
        FAIL=$((FAIL + 1))
        FAIL_NAMES+=("$name")
    fi
    set_detail "$name" "$(details_for "$name" "$log")"
    local detail
    detail=$(get_detail "$name")
    [ -n "$detail" ] && printf "  %s" "$detail"
    printf "\n"
}

details_for() {
    local name=$1 log=$2
    case "$name" in
        format)
            tail -n 1 "$log" 2>/dev/null || true
            ;;
        lint | docstrings)
            grep -E 'All checks passed|Found [0-9]+ errors?' "$log" | tail -n 1 || true
            ;;
        docstrings-strict)
            tail -n 1 "$log" 2>/dev/null || true
            ;;
        type-check)
            grep -E '^Success:|^Found [0-9]+ errors?' "$log" | tail -n 1 || true
            ;;
        metrics)
            grep -E '^Code metrics (passed|check failed)' "$log" | head -n 1 || true
            ;;
        tests)
            local passed coverage
            passed=$(grep -oE '[0-9]+ passed' "$log" | tail -n 1 || true)
            coverage=$(awk '/^TOTAL/{print $NF}' "$log" | tail -n 1 || true)
            printf "%s%s" "${passed:-tests failed}" "${coverage:+ · coverage $coverage}"
            ;;
    esac
}

contains() {
    local needle=$1; shift
    for item; do [ "$item" = "$needle" ] && return 0; done
    return 1
}

set_detail() {
    local name=$1 value=$2
    case "$name" in
        format) DETAIL_FORMAT=$value ;;
        lint) DETAIL_LINT=$value ;;
        docstrings) DETAIL_DOCSTRINGS=$value ;;
        docstrings-strict) DETAIL_DOCSTRINGS_STRICT=$value ;;
        type-check) DETAIL_TYPE_CHECK=$value ;;
        metrics) DETAIL_METRICS=$value ;;
        tests) DETAIL_TESTS=$value ;;
    esac
}

get_detail() {
    local name=$1
    case "$name" in
        format) printf "%s" "$DETAIL_FORMAT" ;;
        lint) printf "%s" "$DETAIL_LINT" ;;
        docstrings) printf "%s" "$DETAIL_DOCSTRINGS" ;;
        docstrings-strict) printf "%s" "$DETAIL_DOCSTRINGS_STRICT" ;;
        type-check) printf "%s" "$DETAIL_TYPE_CHECK" ;;
        metrics) printf "%s" "$DETAIL_METRICS" ;;
        tests) printf "%s" "$DETAIL_TESTS" ;;
    esac
}

print_failures() {
    if [ "${#FAIL_NAMES[@]}" -eq 0 ]; then
        return
    fi

    for name in "${FAIL_NAMES[@]}"; do
        local log="work/${name}.log"
        printf "\n${Y}%s${N}\n${Y}── %s details ──${N}\n" "$SEP" "$name"
        [ -f "$log" ] && cat "$log"
    done
}

print_summary() {
    local total=$((PASS + FAIL))
    printf "\n${B}%s${N}\n" "$SEP"
    printf "${B} %-20s  %-10s  %s${N}\n" "Check" "Status" "Details"
    printf "${B}%s${N}\n" "$SEP"

    for name in format lint docstrings docstrings-strict type-check metrics tests; do
        local status
        if contains "$name" "${FAIL_NAMES[@]+"${FAIL_NAMES[@]}"}"; then
            status="${R}✘ FAIL${N}"
        else
            status="${G}✔ pass${N}"
        fi
        printf " %-20s  %-19b  %s\n" "$name" "$status" "$(get_detail "$name")"
    done

    printf "${B}%s${N}\n" "$SEP"
    if [ "$FAIL" -eq 0 ]; then
        printf " ${G}${B}All %d local checks passed.${N}\n\n" "$total"
    else
        printf " ${R}${B}%d of %d local checks failed.${N}\n\n" "$FAIL" "$total"
    fi
}

printf "\n${B}Running local quality checks…${N}\n\n"

run "format"            work/format.log            uv run ruff format src/ scripts/
run "lint"              work/lint.log              uv run ruff check src/ scripts/
run "docstrings"        work/docstrings.log        uv run ruff check src/ --select D --ignore D100,D104
run "docstrings-strict" work/docstrings-strict.log uv run python scripts/check_google_docstrings.py
run "type-check"        work/type-check.log        uv run mypy src/
run "metrics"           work/metrics.log           uv run python scripts/code_metrics.py

printf " %-20s  " "tests"
uv run pytest >work/tests.log 2>&1; rc=$?
[ "$rc" -eq 5 ] && rc=0
set_detail "tests" "$(details_for tests work/tests.log)"
if [ "$rc" -eq 0 ]; then
    printf "${G}✔ pass${N}"
    PASS=$((PASS + 1))
else
    printf "${R}✘ FAIL${N}"
    FAIL=$((FAIL + 1))
    FAIL_NAMES+=("tests")
fi
[ -n "$(get_detail tests)" ] && printf "  %s" "$(get_detail tests)"
printf "\n"

print_failures
print_summary

exit "$FAIL"
