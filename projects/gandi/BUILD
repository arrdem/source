package(default_visibility = ["//visibility:public"])

py_library(
    name = "gandi",
    srcs = glob(["src/python/gandi/client.py"]),
    imports = [
        "src/python"
    ],
    deps = [
        py_requirement("requests"),
    ],
)
