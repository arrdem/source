# WORKSPACE
#
# This file exists to configure the Bazel (https://bazel.build/) build tool to our needs.
# Particularly, it installs rule definitions and other capabilities which aren't in Bazel core.
# In the future we may have our own modifications to this config.

# Install the blessed Python and PyPi rule support
# From https://github.com/bazelbuild/rules_python

workspace(
    name = "arrdem_source",
)

load(
    "@bazel_tools//tools/build_defs/repo:http.bzl",
    "http_archive",
    "http_file",
)
load(
    "@bazel_tools//tools/build_defs/repo:git.bzl",
    "git_repository",
)

####################################################################################################
# Skylib
####################################################################################################
git_repository(
    name = "bazel_skylib",
    remote = "https://github.com/bazelbuild/bazel-skylib.git",
    tag = "1.0.3",
)
load("@bazel_skylib//:workspace.bzl", "bazel_skylib_workspace")
bazel_skylib_workspace()

####################################################################################################
# Python support
####################################################################################################
register_toolchains("//tools/python:toolchain")

# Using rules_python at a more recent SHA than the last release like a baws
git_repository(
    name = "rules_python",
    remote = "https://github.com/bazelbuild/rules_python.git",
    tag = "0.3.0",
    # commit = "...",
)

# pip package pinnings need to be initialized.
# this generates a bunch of bzl rules so that each pip dep is a bzl target
load("@rules_python//python:pip.bzl", "pip_install")

pip_install(
    name = "arrdem_source_pypi",
    requirements = "//tools/python:requirements.txt",
)

# git_repository(
#     name = "rules_zapp",
#     remote = "https://github.com/arrdem/rules_zapp.git",
#     tag = "0.1.2",
# )

local_repository(
    name = "rules_zapp",
    path = "/home/arrdem/doc/hobby/programming/lang/python/rules_zapp",
)
