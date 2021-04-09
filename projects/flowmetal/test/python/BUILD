py_library(
    name = "conftest",
    srcs = [
       "conftest.py"
    ],
    imports = [
        "."
    ],
)

py_pytest(
    name = "test",
    srcs = glob(["*.py"]),
    deps = [
        "//projects/flowmetal:lib",
        ":conftest",
        py_requirement("pytest-cov"),
    ],
    args = ["--cov-report", "term", "--cov=flowmetal"],
)
