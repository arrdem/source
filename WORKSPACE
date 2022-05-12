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

# Using rules_python at a more recent SHA than the last release like a baws
git_repository(
    name = "rules_python",
    remote = "https://github.com/bazelbuild/rules_python.git",
    # tag = "0.4.0",
    commit = "888fa20176cdcaebb33f968dc7a8112fb678731d",
)

register_toolchains("//tools/python:python3_toolchain")

# pip package pinnings need to be initialized.
# this generates a bunch of bzl rules so that each pip dep is a bzl target
load("@rules_python//python:pip.bzl", "pip_parse")

pip_parse(
    name = "arrdem_source_pypi",
    requirements_lock = "//tools/python:requirements.txt",
    python_interpreter_target = "//tools/python:pythonshim",
)

# Load the starlark macro which will define your dependencies.
load("@arrdem_source_pypi//:requirements.bzl", "install_deps")

# Call it to define repos for your requirements.
install_deps()

git_repository(
    name = "rules_zapp",
    remote = "https://github.com/arrdem/rules_zapp.git",
    commit = "d7a0382927fb8a68115b560f4fee7dca743068f8",
    # tag = "0.1.2",
)

# local_repository(
#     name = "rules_zapp",
#     path = "/home/arrdem/doc/hobby/programming/lang/python/rules_zapp",
# )
