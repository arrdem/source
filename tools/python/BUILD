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
    name = "python_runtime",
    interpreter_path = "/usr/bin/python3",
    python_version = "PY3",
    visibility = ["//visibility:public"],
)

py_runtime_pair(
    name = "runtime",
    py2_runtime = None,
    py3_runtime = ":python_runtime",
)

toolchain(
    name = "toolchain",
    toolchain = ":runtime",
    toolchain_type = "@bazel_tools//tools/python:toolchain_type",
)

py_binary(
    name = "autoflake",
    main = "autoflake_shim.py",
    deps = [
        py_requirement("autoflake"),
    ]
)

py_binary(
    name = "black",
    main = "black_shim.py",
    deps = [
        py_requirement("black"),
    ]
)

py_binary(
    name = "isort",
    main = "isort_shim.py",
    deps = [
        py_requirement("isort"),
    ]
)

py_binary(
    name = "sphinx",
    main = "sphinx_shim.py",
    deps = [
        py_requirement("click"),
        py_requirement("recommonmark"),
        py_requirement("sphinx"),
        py_requirement("sphinxcontrib-openapi"),
        py_requirement("sphinxcontrib-programoutput"),
        py_requirement("livereload"),
    ]
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
    ]
)

py_binary(
    name = "unify",
    main = "unify_shim.py",
    deps = [
        py_requirement("unify"),
    ]
)

py_binary(
    name = "openapi",
    main = "openapi_shim.py",
    deps = [
        py_requirement("openapi-spec-validator"),
    ]
)

# WARNING: YAMLLINT is GLP3'd code. Do not extend, modify or depend on this as a lib.
py_binary(
    name = "yamllint",
    main = "yamllint_shim.py",
    deps = [
        py_requirement("yamllint"),
    ]
)

py_binary(
    name = "reqsort",
    main = "reqsort.py",
    deps = [
        py_requirement("click"),
    ]
)


py_binary(
    name = "templater",
    main = "templater.py",
    deps = [
        py_requirement("click"),
        py_requirement("jinja2"),
        py_requirement("PyYAML"),
    ]
)

py_binary(
    name = "xfmt",
    main = "xfmt.py",
    deps = [
        py_requirement("beautifulsoup4"),
        py_requirement("click"),
        py_requirement("lxml"),
    ]
)
