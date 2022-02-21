#!/usr/bin/env bash

cd "$(dirname $(realpath "$0"))"

exec bazel run :updater -- \
    --config $(realpath ./config.yml) \
    --templates $(realpath src/resources/zonefiles)
