#!/usr/bin/env bash
set -euox pipefail
cd "$(git rev-parse --show-toplevel)"
bazel build //tools/python/...

DIRS=(tools projects)

bazel-bin/tools/python/autoflake -r "${DIRS[@]}"
bazel-bin/tools/python/isort --check "${DIRS[@]}"
bazel-bin/tools/python/unify --quote '"' -cr "${DIRS[@]}"
bazel-bin/projects/reqman/reqman lint tools/python/requirements.txt

for f in $(find . -type f -name "openapi.yaml"); do
  bazel-bin/tools/python/openapi "${f}" && echo "Schema $f OK"
done

for f in $(find . -type f -name "openapi.yaml"); do
  bazel-bin/tools/python/yamllint -c tools/yamllint/yamllintrc "${f}"
done
