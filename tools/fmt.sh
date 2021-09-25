#!/usr/bin/env bash
set -euox pipefail
cd "$(git rev-parse --show-toplevel)"

bazel build //tools/... //projects/reqman

DIRS=(projects tools)

function brl() {
    bin="$1"
    shift
    bazel run "//${bin}" -- "$@"
    return "$?"
}

brl tools/autoflake --remove-all-unused-imports -ir "${DIRS[@]}"
brl tools/isort     "${DIRS[@]}"
brl tools/unify     --quote '"' -ir "${DIRS[@]}"
brl projects/reqman clean tools/python/requirements.txt
