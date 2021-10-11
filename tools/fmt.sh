#!/usr/bin/env bash
set -euox pipefail
cd "$(git rev-parse --show-toplevel)"

bazel build //tools/... //projects/reqman

DIRS=(projects tools)

function brl() {
    bin="$1"
    shift
    bazel build "//${bin}"
    "bazel-bin/${bin}/$(basename ${bin})" "$@"
    return "$?"
}

for d in "${DIRS[@]}"; do
    brl tools/autoflake --remove-all-unused-imports -ir $(realpath "$d")
    brl tools/isort $(realpath "$d")
    brl tools/unify --quote '"' -ir $(realpath "$d")
done

brl projects/reqman clean tools/python/requirements.txt
