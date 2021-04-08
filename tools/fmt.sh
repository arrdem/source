#!/usr/bin/env bash
set -euox pipefail
cd "$(git rev-parse --show-toplevel)"

bazel build //tools/python/...

DIRS=(*)

bazel-bin/tools/python/autoflake -ir "${DIRS[@]}"
bazel-bin/tools/python/black "${DIRS[@]}"
bazel-bin/tools/python/isort "${DIRS[@]}"
bazel-bin/tools/python/unify --quote '"' -ir "${DIRS[@]}"
bazel-bin/tools/python/reqsort --execute tools/python/requirements.txt
