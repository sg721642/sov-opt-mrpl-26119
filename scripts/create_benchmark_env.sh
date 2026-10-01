#!/usr/bin/env bash
# Creates an isolated benchmark environment containing highspy and scipy
# for differential validation. This environment is kept strictly separate
# from the sovereign core solver environment (.venv).

set -euo pipefail

BENCH_VENV="${1:-.venv-benchmark}"
PYTHON="${PYTHON:-python3}"

echo "Creating isolated benchmark environment at ${BENCH_VENV}..."
unset PYTHONHOME || true
"${PYTHON}" -m venv "${BENCH_VENV}"

echo "Installing reference solvers (highspy, scipy)..."
"${BENCH_VENV}/bin/pip" install --upgrade pip
"${BENCH_VENV}/bin/pip" install highspy scipy

echo "Benchmark environment created successfully."
echo "To run external validation, execute:"
echo "  SOVOPT_BENCHMARK_PYTHON=${BENCH_VENV}/bin/python .venv/bin/python scripts/generate_reports.py"
