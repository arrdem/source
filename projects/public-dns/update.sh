#!/usr/bin/env bash

exec bazel run :updater -- \
    --config $(realpath ./config.yml) \
    --templates $(realpath src/resources/zonefiles)
