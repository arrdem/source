#!/usr/bin/env bash
set -euox pipefail
cd "$(git rev-parse --show-toplevel)"
bazel build //tools/python/...

DIRS=(tools projects)

function brl() {
    bin="$1"
    shift
    bazel build "//${bin}"
    "bazel-bin/${bin}/$(basename ${bin})" "$@"
    return "$?"
}

brl tools/autoflake -r "${DIRS[@]}"
brl tools/isort --check "${DIRS[@]}"
brl tools/unify --quote '"' -cr "${DIRS[@]}"
brl tools/reqman lint tools/python/requirements.txt

# OpenAPI specific junk
for f in $(find . -type f -name "openapi.yaml"); do
  brl tools/openapi "${f}" && echo "Schema $f OK"
  brl tools/yamllint -c tools/yamllint/yamllintrc "${f}"
done
