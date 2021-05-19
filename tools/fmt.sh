#!/usr/bin/env bash
set -euox pipefail
cd "$(git rev-parse --show-toplevel)"

bazel build //tools/python/... //projects/reqsort

DIRS=(projects tools)

bazel-bin/tools/python/autoflake -ir "${DIRS[@]}"
bazel-bin/tools/python/isort "${DIRS[@]}"
bazel-bin/tools/python/unify --quote '"' -ir "${DIRS[@]}"
bazel-bin/projects/reqsort/reqsort --execute tools/python/requirements.txt
