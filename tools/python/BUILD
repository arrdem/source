load("@rules_python//python:defs.bzl",
     "py_runtime_pair"
)

package(default_visibility = ["//visibility:public"])

licenses(["notice"])

exports_files([
    "defs.bzl",
    "bzl_pytest_shim.py",
    "bzl_unittest_shim.py",
])

py_runtime(
    name = "python3_runtime",
    files = [],
    interpreter_path = "/usr/bin/python3.9",
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
    deps = [
        py_requirement("requests"),
        py_requirement("requirements-parser"),
    ]
)

py_binary(
    name = "openapi",
    main = "openapi_shim.py",
    deps = [
        py_requirement("openapi-spec-validator"),
    ]
)
