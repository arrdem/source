#!/usr/bin/env bash
set -euox pipefail
cd "$(git rev-parse --show-toplevel)"
bazel build //tools/python/...

DIRS=(*)

bazel-bin/tools/python/autoflake -r "${DIRS[@]}"
bazel-bin/tools/python/black --check "${DIRS[@]}"
bazel-bin/tools/python/isort --check "${DIRS[@]}"
bazel-bin/tools/python/unify --quote '"' -cr "${DIRS[@]}"
bazel-bin/tools/python/reqsort --dryrun tools/python/requirements.txt

for f in $(find . -type f -name "openapi.yaml"); do
  bazel-bin/tools/python/openapi "${f}" && echo "Schema $f OK"
done

for f in $(find . -type f -name "openapi.yaml"); do
  bazel-bin/tools/python/yamllint -c tools/yamllint/yamllintrc "${f}"
done
