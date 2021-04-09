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
        "//projects/calf:lib",
        ":conftest",
        py_requirement("pytest-cov"),
    ],
    args = ["--cov-report", "term", "--cov=calf"],
)
