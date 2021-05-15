py_library(
    name = "damm",
    srcs = [
        "damm.py",
    ],
    imports = [
        "."
    ],
    visibility = [
        "//visibility:public",
    ]
)

py_pytest(
    name = "test_damm",
    srcs = glob(["test_*.py"]),
    deps = [
        ":damm",
    ]
)
