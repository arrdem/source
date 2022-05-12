load("@rules_python//python:defs.bzl",
     "py_runtime_pair",
)

load("@arrdem_source_pypi//:requirements.bzl", "all_requirements")

package(default_visibility = ["//visibility:public"])

licenses(["notice"])

exports_files([
    "defs.bzl",
    "bzl_pytest_shim.py",
    "bzl_unittest_shim.py",
    "pythonshim",
])

py_runtime(
    name = "python3_runtime",
    files = [],
    interpreter = ":pythonshim",
    python_version = "PY3",
    visibility = ["//visibility:public"],
)

py_runtime_pair(
    name = "python_runtime",
    py2_runtime = None,
    py3_runtime = ":python3_runtime",
)

toolchain(
    name = "python3_toolchain",
    toolchain = ":python_runtime",
    toolchain_type = "@bazel_tools//tools/python:toolchain_type",
)

py_pytest(
    name = "test_licenses",
    srcs = [
        "test_licenses.py",
    ],
    data = [
        "requirements.txt",
    ],
    deps = all_requirements,
)
