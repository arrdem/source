package(default_visibility = ["//visibility:public"])

py_library(
    name = "lib",
    srcs = glob(["src/python/**/*.py"]),
    imports = ["src/python"],
    deps = [
        py_requirement("prompt-toolkit"),
    ]
)
