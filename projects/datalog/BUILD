py_library(
    name = "datalog",
    srcs = glob(["src/python/**/*.py"]),
    imports = [
        "src/python",
    ],
    visibility = [
        "//visibility:public",
    ]
)

py_pytest(
    name = "test_datalog",
    srcs = glob(["test/python/**/*.py"]),
    deps = [
        ":datalog",
    ]
)
